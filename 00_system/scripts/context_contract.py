from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from context_integrity import inspect_page, load_memory_policy
from wiki_lib import PrivatePolicyError, load_private_policy, parse_frontmatter


CONTROL_CLOSURE = ("PRODUCT_SPEC.md", "ARCHITECTURE.md", "TASKS.md")
DEFAULT_REQUIRED_KINDS = ("current_control", "active_decision", "open_risk")


def default_contract(task_id: str) -> dict[str, object]:
    return {
        "task_id": task_id,
        "required_kinds": list(DEFAULT_REQUIRED_KINDS),
        "max_age_days": {"active_decision": 180, "open_risk": 30},
        "max_cards": 6,
        "token_budget": 6000,
        "missing_policy": "block_for_p1_p0",
    }


def stable_task_id(query: str) -> str:
    return f"search-{hashlib.sha256(query.encode('utf-8')).hexdigest()[:16]}"


def estimate_tokens(text: str) -> int:
    cjk_count = len(re.findall(r"[\u4e00-\u9fff]", text))
    other_count = len(text) - cjk_count
    return cjk_count + (other_count + 3) // 4


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _file_hash(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _read_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} root value must be an object")
    return payload


def _git_head(repo_root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout.strip() if completed.returncode == 0 else "unavailable"


def _query_terms(query: str) -> list[str]:
    return list(dict.fromkeys(re.findall(r"[\u4e00-\u9fff]{2,}|[a-z0-9]+", query.lower())))


def _selected_line(text: str, query: str) -> str:
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip() and line.strip() != "---" and not line.lstrip().startswith("#")
    ]
    terms = _query_terms(query)
    for line in lines:
        lowered = line.lower()
        if any(term in lowered for term in terms) and estimate_tokens(line) <= 120:
            return line
    for line in lines:
        if estimate_tokens(line) <= 120:
            return line
    return ""


def _control_items(repo_root: Path, query: str) -> tuple[list[dict[str, object]], list[str]]:
    controls: list[dict[str, object]] = []
    missing: list[str] = []
    for name in CONTROL_CLOSURE:
        path = repo_root / name
        if not path.exists() or not path.is_file():
            missing.append(f"current_control:{name}")
            continue
        text = path.read_text(encoding="utf-8")
        controls.append(
            {
                "path": name,
                "authority": "L1",
                "hash": _sha256_bytes(text.encode("utf-8")),
                "excerpt": _selected_line(text, query),
            }
        )
    return controls, missing


def _memory_item(
    repo_root: Path,
    wiki_root: Path,
    query: str,
    policy: dict[str, object],
    now: datetime,
) -> tuple[dict[str, object], list[str]]:
    context_path = repo_root / "wiki.context.json"
    if not context_path.exists():
        return {}, ["project_memory"]
    context = _read_json(context_path)
    raw_path = str(context.get("project_memory") or "").strip()
    if not raw_path:
        return {}, ["project_memory"]
    path = Path(raw_path)
    if not path.is_absolute():
        path = wiki_root / path
    memory_policy = dict(policy)
    memory_policy["require_provenance"] = False
    memory_policy["max_age_days"] = 30
    inspected = inspect_page(path, policy=memory_policy, today=now.date())
    if inspected["status"] == "quarantined":
        return {"path": str(raw_path), "trust_state": "quarantined", "reasons": inspected["reasons"]}, ["project_memory"]
    text = path.read_text(encoding="utf-8")
    _frontmatter, body = parse_frontmatter(text)
    return {
        "path": str(raw_path).replace("\\", "/"),
        "authority": "L2",
        "hash": _sha256_bytes(text.encode("utf-8")),
        "trust_state": inspected["status"],
        "reasons": inspected["reasons"],
        "excerpt": _selected_line(body, query),
    }, []


def _kind(candidate: dict[str, object]) -> str:
    explicit = str(candidate.get("kind") or "").strip()
    if explicit:
        return explicit
    page_type = str(candidate.get("page_type") or "").strip()
    if page_type in {"项目决策", "ADR"}:
        return "active_decision"
    if page_type == "项目风险":
        return "open_risk"
    return "supporting_context"


def _candidate_items(
    candidates: list[dict[str, object]],
    *,
    wiki_root: Path,
    policy: dict[str, object],
    contract: dict[str, object],
    now: datetime,
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[str]]:
    inspected_items: list[dict[str, object]] = []
    excluded: list[dict[str, object]] = []
    max_age = contract.get("max_age_days") if isinstance(contract.get("max_age_days"), dict) else {}
    for candidate in candidates:
        raw_path = str(candidate.get("path") or "").strip()
        if not raw_path:
            continue
        path = Path(raw_path)
        if not path.is_absolute():
            path = wiki_root / path
        kind = _kind(candidate)
        card_policy = dict(policy)
        card_policy["require_provenance"] = True
        if kind in max_age:
            card_policy["max_age_days"] = int(max_age[kind])
        inspected = inspect_page(path, policy=card_policy, today=now.date())
        item = {
            "id": str(inspected.get("id") or f"path-{hashlib.sha256(raw_path.encode('utf-8')).hexdigest()[:16]}"),
            "path": raw_path.replace("\\", "/"),
            "title": str(candidate.get("title") or path.stem),
            "heading": str(candidate.get("heading") or "").strip(),
            "kind": kind,
            "authority": "L2",
            "score": int(candidate.get("score") or 0),
            "trust_state": inspected["status"],
            "reasons": inspected["reasons"],
            "hash": _file_hash(path) if path.exists() and path.is_file() else "",
            "snippet": str(candidate.get("snippet") or "").strip(),
            "source_notes": candidate.get("source_notes") if isinstance(candidate.get("source_notes"), list) else [],
            "source_refs": candidate.get("source_refs") if isinstance(candidate.get("source_refs"), list) else [],
        }
        if inspected["status"] != "trusted":
            excluded.append(item)
        else:
            inspected_items.append(item)

    by_id: dict[str, list[dict[str, object]]] = {}
    for item in inspected_items:
        by_id.setdefault(str(item["id"]), []).append(item)
    conflicts = sorted(item_id for item_id, items in by_id.items() if len(items) > 1)
    if conflicts:
        conflict_set = set(conflicts)
        kept: list[dict[str, object]] = []
        for item in inspected_items:
            if item["id"] in conflict_set:
                item["trust_state"] = "quarantined"
                item["reasons"] = [f"duplicate_id:{item['id']}"]
                excluded.append(item)
            else:
                kept.append(item)
        inspected_items = kept
    inspected_items.sort(key=lambda item: (-int(item["score"]), str(item["path"])))
    return inspected_items, excluded, conflicts


def _base_context(query: str, status: str, budget: int, controls: list[dict[str, object]], memory: dict[str, object]) -> str:
    lines = [
        "# OTW Context Pack",
        f"- query: {query}",
        f"- status: {status}",
        f"- token_budget: {budget}",
        "- L1 controls: " + ", ".join(f"{item['path']}@{str(item['hash'])[:12]}" for item in controls),
    ]
    if memory:
        lines.append(
            f"- project_memory: {memory.get('path', '-')}@{str(memory.get('hash', ''))[:12]} [{memory.get('trust_state', 'missing')}]"
        )
    for item in controls:
        if item.get("excerpt"):
            lines.append(f"- {item['path']}: {item['excerpt']}")
    if memory.get("excerpt"):
        lines.append(f"- project_memory excerpt: {memory['excerpt']}")
    return "\n".join(lines) + "\n"


def _card_block(item: dict[str, object]) -> str:
    notes = ", ".join(str(value) for value in item.get("source_notes", [])) or "-"
    refs = ", ".join(str(value) for value in item.get("source_refs", [])) or "-"
    return (
        f"\n## {item['title']}\n"
        f"- id: {item['id']}\n"
        f"- path: {item['path']}\n"
        f"- kind: {item['kind']}\n"
        f"- trust: {item['trust_state']}\n"
        f"- heading: {item['heading'] or '-'}\n"
        f"- source_notes: {notes}\n"
        f"- source_refs: {refs}\n"
        f"> {item['snippet']}\n"
    )


def _write_receipt(repo_root: Path, task_id: str, receipt: dict[str, object]) -> Path:
    safe_id = re.sub(r"[^A-Za-z0-9._-]+", "-", task_id).strip("-._") or "context"
    directory = repo_root / ".obsidiantowiki" / "context-receipts"
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / f"{safe_id}.json"
    temporary = destination.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(destination)
    return destination


def build_context(
    *,
    repo_root: Path,
    wiki_root: Path,
    query: str,
    task_id: str,
    candidates: list[dict[str, object]],
    contract: dict[str, object] | None = None,
    now: datetime | None = None,
    write_receipt: bool = True,
) -> dict[str, object]:
    resolved_repo = repo_root.expanduser().resolve()
    resolved_wiki = wiki_root.expanduser().resolve()
    generated_at = now or datetime.now(timezone.utc)
    active_contract = dict(contract or default_contract(task_id))
    active_contract["task_id"] = task_id
    max_cards_value = active_contract.get("max_cards")
    max_cards = max(0, min(6, int(6 if max_cards_value is None else max_cards_value)))
    token_budget = int(active_contract.get("token_budget") or 6000)
    if token_budget < 100:
        raise ValueError("token_budget must be at least 100")

    policy = load_memory_policy()
    try:
        private_policy = load_private_policy(resolved_wiki)
    except PrivatePolicyError:
        private_policy = {"schema_version": 1, "ai_access": {"excluded_paths": [], "excluded_globs": []}}
        policy_invalid = True
    else:
        policy_invalid = False
    policy["vault_root"] = str(resolved_wiki)
    policy["private_policy"] = private_policy

    controls, missing = _control_items(resolved_repo, query)
    memory, memory_missing = _memory_item(resolved_repo, resolved_wiki, query, policy, generated_at)
    missing.extend(memory_missing)
    trusted, excluded, conflicts = _candidate_items(
        candidates,
        wiki_root=resolved_wiki,
        policy=policy,
        contract=active_contract,
        now=generated_at,
    )
    if policy_invalid:
        missing.append("private_policy")

    required_kinds = [str(item) for item in active_contract.get("required_kinds", []) if str(item).strip()]
    available_kinds = {str(item["kind"]) for item in trusted}
    if len(controls) == len(CONTROL_CLOSURE):
        available_kinds.add("current_control")

    provisional_status = "missing" if missing else "ready"
    context_text = _base_context(query, provisional_status, token_budget, controls, memory)
    selected: list[dict[str, object]] = []
    dropped: list[dict[str, object]] = []
    for item in trusted:
        if len(selected) >= max_cards:
            dropped.append(item)
            continue
        block = _card_block(item)
        if estimate_tokens(context_text + block) > token_budget:
            dropped.append(item)
            continue
        selected.append(item)
        context_text += block

    selected_kinds = {str(item["kind"]) for item in selected} | ({"current_control"} if len(controls) == len(CONTROL_CLOSURE) else set())
    for kind in required_kinds:
        if kind not in selected_kinds and kind not in missing:
            missing.append(kind)
    missing = list(dict.fromkeys(missing))
    status = "missing" if missing else "degraded" if excluded or conflicts or dropped else "ready"
    if status != provisional_status:
        context_text = context_text.replace(f"- status: {provisional_status}", f"- status: {status}", 1)

    l0 = {"git_head": _git_head(resolved_repo)}
    l1_files = [{key: item[key] for key in ("path", "hash", "authority")} for item in controls]
    card_receipts = [
        {key: item[key] for key in ("id", "path", "kind", "hash", "trust_state", "score")}
        for item in selected
    ]
    used_tokens = estimate_tokens(context_text)
    stable_payload = {
        "query": query,
        "task_id": task_id,
        "contract": active_contract,
        "l0": l0,
        "l1_files": l1_files,
        "project_memory": {key: memory.get(key) for key in ("path", "hash", "trust_state")},
        "cards": card_receipts,
        "missing": missing,
        "conflicts": conflicts,
        "status": status,
        "context": context_text,
    }
    content_hash = _sha256_bytes(json.dumps(stable_payload, ensure_ascii=False, sort_keys=True).encode("utf-8"))
    receipt = {
        "schema_version": 1,
        **stable_payload,
        "budget": {"limit": token_budget, "used": used_tokens, "max_cards": max_cards},
        "excluded": [{key: item[key] for key in ("id", "path", "trust_state", "reasons")} for item in excluded],
        "dropped": [str(item["id"]) for item in dropped],
        "degradation": status if status != "ready" else "none",
        "generated_at": generated_at.isoformat(),
        "content_hash": content_hash,
    }
    receipt_path = _write_receipt(resolved_repo, task_id, receipt) if write_receipt else None
    return {
        "schema_version": 1,
        "status": status,
        "contract": active_contract,
        "controls": controls,
        "project_memory": memory,
        "cards": selected,
        "excluded": excluded,
        "dropped": dropped,
        "missing": missing,
        "conflicts": conflicts,
        "token_usage": {"limit": token_budget, "used": used_tokens},
        "content": context_text,
        "context": context_text,
        "content_hash": content_hash,
        "receipt": receipt,
        "receipt_path": str(receipt_path) if receipt_path else "",
    }
