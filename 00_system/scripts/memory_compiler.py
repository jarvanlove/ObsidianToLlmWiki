from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from wiki_lib import parse_frontmatter, render_markdown


DEFAULT_POLICY_PATH = Path(__file__).resolve().parents[1] / "registry" / "memory_policy.json"
DEFAULT_KIND_RULES = {
    "decision": {"prefix": "DEC", "review": False},
    "open_risk": {"prefix": "RISK", "review": False},
    "root_cause": {"prefix": "ROOT", "review": False},
    "milestone": {"prefix": "MILE", "review": False},
    "capability_observation": {"prefix": "CAP", "review": True},
}
SENSITIVE_VALUE = re.compile(r"(?i)(?:api[_-]?key|password|secret)\s*[:=]\s*\S+")
PRIVATE_ABSOLUTE_PATH = re.compile(r"(?:[A-Za-z]:\\|/(?:Users|home)/)")
CORE_PROJECTION_NAMES = (
    "概览.md",
    "架构.md",
    "决策.md",
    "任务.md",
    "风险.md",
    "时间线.md",
    "project.memory.md",
)
PROJECTION_START = "<!-- OBSIDIANTOWIKI:CURRENT_PROJECTION_START -->"
PROJECTION_END = "<!-- OBSIDIANTOWIKI:CURRENT_PROJECTION_END -->"
PROJECTION_TYPES = {
    "概览.md": ("项目概览", "概览"),
    "架构.md": ("项目架构", "架构"),
    "决策.md": ("项目决策", "决策"),
    "任务.md": ("项目任务", "任务"),
    "风险.md": ("项目风险", "风险"),
    "时间线.md": ("项目时间线", "时间线"),
    "project.memory.md": ("项目运行记忆", "运行记忆"),
}


def load_policy(path: Path = DEFAULT_POLICY_PATH) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read memory policy: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError("memory policy requires schema_version=1")
    return payload


def write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        os.replace(temp_name, path)
    finally:
        temporary = Path(temp_name)
        if temporary.exists():
            temporary.unlink()


def normalized_key(value: object) -> str:
    return "-".join(str(value or "").strip().lower().split())


def kind_rules(policy: dict[str, Any]) -> dict[str, dict[str, Any]]:
    cards = policy.get("memory_cards") if isinstance(policy.get("memory_cards"), dict) else {}
    configured = cards.get("kind_rules") if isinstance(cards.get("kind_rules"), dict) else {}
    rules = {name: dict(rule) for name, rule in DEFAULT_KIND_RULES.items()}
    for name, rule in configured.items():
        if name in rules and isinstance(rule, dict):
            rules[name].update(rule)
    return rules


def stable_card_id(project_slug: str, kind: str, stable_key: str, rules: dict[str, dict[str, Any]]) -> str:
    prefix = str(rules[kind].get("prefix") or "MEM").upper()
    digest = hashlib.sha256(f"{project_slug}|{kind}|{stable_key}".encode("utf-8")).hexdigest()[:12].upper()
    return f"{prefix}-{digest}"


def content_hash(kind: str, stable_key: str, summary: str, evidence_refs: list[str], destination: str) -> str:
    payload = {
        "kind": kind,
        "stable_key": stable_key,
        "summary": summary,
        "evidence_refs": evidence_refs,
        "destination": destination,
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def is_sensitive(candidate: dict[str, Any], summary: str) -> bool:
    return bool(candidate.get("sensitive")) or bool(SENSITIVE_VALUE.search(summary)) or bool(
        PRIVATE_ABSOLUTE_PATH.search(summary)
    )


def string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def load_existing_cards(memory_dir: Path) -> tuple[dict[str, tuple[Path, dict[str, Any], str]], dict[str, str]]:
    by_id: dict[str, tuple[Path, dict[str, Any], str]] = {}
    key_to_id: dict[str, str] = {}
    if not memory_dir.exists():
        return by_id, key_to_id
    for path in sorted(memory_dir.glob("*.md")):
        try:
            frontmatter, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError) as exc:
            raise ValueError(f"cannot compile over invalid memory card {path.name}: {exc}") from exc
        card_id = str(frontmatter.get("id") or "").strip()
        stable_key = normalized_key(frontmatter.get("stable_key"))
        if not card_id or not stable_key or card_id in by_id:
            raise ValueError(f"invalid or duplicate memory identity in {path.name}")
        by_id[card_id] = (path, dict(frontmatter), body)
        if frontmatter.get("status") == "active":
            key_to_id[stable_key] = card_id
    return by_id, key_to_id


def render_card(frontmatter: dict[str, Any], summary: str) -> str:
    return render_markdown(frontmatter, f"# {summary}\n\n{summary}")


def estimate_tokens(content: str) -> int:
    """Return a deterministic conservative estimate without a tokenizer dependency."""
    ascii_chars = sum(1 for character in content if ord(character) < 128)
    return max(1, (ascii_chars + 3) // 4 + (len(content) - ascii_chars))


def _project_cards(memory_dir: Path) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    if not memory_dir.exists():
        return cards
    for path in sorted(memory_dir.glob("*.md")):
        frontmatter, _body = parse_frontmatter(path.read_text(encoding="utf-8"))
        if frontmatter.get("status") != "active":
            continue
        card = dict(frontmatter)
        card["path"] = path
        cards.append(card)
    return cards


def _bounded_lines(prefix: list[str], entries: list[str], suffix: list[str], budget: int) -> str:
    selected: list[str] = []
    for entry in entries:
        candidate = "\n".join([*prefix, *selected, entry, *suffix]).rstrip() + "\n"
        if estimate_tokens(candidate) > budget:
            continue
        selected.append(entry)
    if not selected:
        selected = ["- 暂无已确认事实。"]
    return "\n".join([*prefix, *selected, *suffix]).rstrip() + "\n"


def compile_projections(
    *,
    wiki_root: Path,
    project_slug: str,
    policy_path: Path = DEFAULT_POLICY_PATH,
    dry_run: bool = False,
    today: date | None = None,
    archive_links: dict[str, str] | None = None,
    allow_unmanaged: bool = False,
) -> dict[str, Any]:
    today = today or date.today()
    project_root = wiki_root / "20_projects" / "active" / project_slug
    cards = _project_cards(project_root / "memory")
    policy = load_policy(policy_path)
    projection_policy = policy.get("projections") if isinstance(policy.get("projections"), dict) else {}
    budgets = projection_policy.get("page_token_budgets") if isinstance(projection_policy.get("page_token_budgets"), dict) else {}
    item_limits = projection_policy.get("page_item_limits") if isinstance(projection_policy.get("page_item_limits"), dict) else {}
    timeline_days = int(projection_policy.get("timeline_days") or 90)
    timeline_limit = int(projection_policy.get("timeline_max_events") or 30)
    archive_links = archive_links or {}

    def items(*kinds: str) -> list[dict[str, Any]]:
        return sorted(
            (card for card in cards if str(card.get("kind") or "") in kinds),
            key=lambda card: (str(card.get("effective_from") or ""), str(card.get("id") or "")),
            reverse=True,
        )

    def entry(card: dict[str, Any]) -> str:
        card_id = str(card.get("id") or "")
        return f"- {card.get('summary')} ([[memory/{card_id}|{card_id}]])"

    all_entries = [entry(card) for card in items(*DEFAULT_KIND_RULES)]
    page_entries: dict[str, list[str]] = {
        "概览.md": all_entries,
        "架构.md": [entry(card) for card in items("root_cause", "decision")],
        "决策.md": [entry(card) for card in items("decision")],
        "任务.md": [entry(card) for card in items("milestone")],
        "风险.md": [entry(card) for card in items("open_risk")],
        "project.memory.md": all_entries,
    }
    for name, limit in item_limits.items():
        if name in page_entries:
            page_entries[name] = page_entries[name][: int(limit)]
    cutoff = today - timedelta(days=timeline_days)
    timeline_cards = [
        card
        for card in items("milestone")
        if str(card.get("effective_from") or "") >= cutoff.isoformat()
    ][:timeline_limit]
    page_entries["时间线.md"] = [
        f"- {card.get('effective_from')} — {card.get('summary')} (`{card.get('id')}`)"
        for card in timeline_cards
    ]

    pages: list[dict[str, Any]] = []
    unmanaged = [
        name
        for name in CORE_PROJECTION_NAMES
        if (project_root / name).exists()
        and PROJECTION_START not in (project_root / name).read_text(encoding="utf-8")
    ]
    if unmanaged and not dry_run and not allow_unmanaged:
        return {
            "status": "blocked",
            "reason": "unmanaged_core_pages_require_migration",
            "unmanaged_pages": unmanaged,
            "pages": [],
            "active_cards": len(cards),
        }
    for name in CORE_PROJECTION_NAMES:
        page_type, label = PROJECTION_TYPES[name]
        title = f"{project_slug} {label}"
        budget = int(budgets.get(name) or 1000)
        prefix = [
            "---",
            f"title: {title}",
            f"type: {page_type}",
            "domain: 项目",
            f"project: {project_slug}",
            "status: 活跃",
            "tags: [有界投影]",
            f"updated: {today.isoformat()}",
            f"summary: {project_slug} 的有界当前{label}投影。",
            "---",
            f"# {title}",
            "",
            PROJECTION_START,
            "",
            "## 当前已确认事实",
            "",
        ]
        suffix = ["", PROJECTION_END]
        archive = archive_links.get(name)
        if archive:
            suffix = ["", f"> 原始页面备份：[[{archive}|查看只读历史]]", *suffix]
        content = _bounded_lines(prefix, page_entries[name], suffix, budget)
        path = project_root / name
        action = "unchanged" if path.exists() and path.read_text(encoding="utf-8") == content else "would_write"
        if not dry_run and action != "unchanged":
            write_text_atomic(path, content)
            action = "written"
        pages.append({"name": name, "path": str(path), "content": content, "token_budget": budget, "action": action})
    return {"status": "dry_run" if dry_run else "compiled", "pages": pages, "active_cards": len(cards)}


def compile_receipt(
    receipt_path: Path,
    *,
    wiki_root: Path,
    project_slug: str,
    policy_path: Path = DEFAULT_POLICY_PATH,
    today: date | None = None,
) -> dict[str, Any]:
    today = today or date.today()
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "blocked", "reasons": [f"invalid_receipt:{type(exc).__name__}"], "cards": []}
    if not isinstance(receipt, dict):
        return {"status": "blocked", "reasons": ["invalid_receipt:root"], "cards": []}
    if receipt.get("schema_version") != 2:
        return {"status": "blocked", "reasons": ["legacy_unstructured"], "cards": []}
    if receipt.get("status") != "resolved":
        return {"status": "blocked", "reasons": ["receipt_not_resolved"], "cards": []}
    gate = (receipt.get("gate_results") or {}).get("verification_evidence") or {}
    if gate.get("status") != "passed" or not isinstance(receipt.get("evidence"), list) or not receipt["evidence"]:
        return {"status": "blocked", "reasons": ["receipt_evidence_gate_not_passed"], "cards": []}

    candidates = receipt.get("knowledge_candidates")
    if not isinstance(candidates, list) or not candidates:
        return {"status": "no_candidates", "reasons": [], "cards": []}

    policy = load_policy(policy_path)
    rules = kind_rules(policy)
    cards_policy = policy.get("memory_cards") if isinstance(policy.get("memory_cards"), dict) else {}
    high_risk_levels = {
        str(item).upper() for item in cards_policy.get("high_risk_review_levels", ["P0", "P1"])
    }
    allowed_destinations = {
        str(item).lower() for item in cards_policy.get("allowed_destinations", ["project", "personal", "shared"])
    }
    memory_dir = wiki_root / "20_projects" / "active" / project_slug / "memory"
    try:
        existing, active_keys = load_existing_cards(memory_dir)
    except ValueError as exc:
        return {"status": "blocked", "reasons": [str(exc)], "cards": []}

    task_id = str(receipt.get("task_id") or receipt_path.stem).strip()
    risk = receipt.get("risk") if isinstance(receipt.get("risk"), dict) else {}
    risk_level = str(risk.get("level") or "P2").upper()
    results: list[dict[str, Any]] = []

    for raw_candidate in candidates:
        if not isinstance(raw_candidate, dict):
            results.append({"action": "rejected", "reasons": ["candidate_not_object"]})
            continue
        candidate = dict(raw_candidate)
        kind = str(candidate.get("kind") or "").strip()
        stable_key = normalized_key(candidate.get("stable_key"))
        summary = str(candidate.get("summary") or "").strip()
        evidence_refs = string_list(candidate.get("evidence_refs"))
        destination = str(candidate.get("destination") or "project").strip().lower()
        if (
            kind not in rules
            or not stable_key
            or not summary
            or not evidence_refs
            or destination not in allowed_destinations
        ):
            results.append({"action": "rejected", "reasons": ["candidate_incomplete_or_unsupported"]})
            continue
        if is_sensitive(candidate, summary):
            results.append({"action": "rejected", "reasons": ["sensitive_content"]})
            continue

        card_id = stable_card_id(project_slug, kind, stable_key, rules)
        digest = content_hash(kind, stable_key, summary, evidence_refs, destination)
        current = existing.get(card_id)
        if current and str(current[1].get("content_hash") or "") == digest:
            results.append(
                {"id": card_id, "action": "unchanged", "status": current[1].get("status", "active")}
            )
            continue

        review_reasons: list[str] = []
        if bool(rules[kind].get("review")):
            review_reasons.append("kind_requires_review")
        if risk_level in high_risk_levels:
            review_reasons.append("high_risk")
        if destination != "project":
            review_reasons.append("cross_layer_destination")
        status = "pending_review" if review_reasons else "active"

        if current:
            disputed_id = f"{card_id}-D{digest[:6].upper()}"
            disputed_path = memory_dir / f"{disputed_id}.md"
            if not disputed_path.exists():
                frontmatter = {
                    "title": summary,
                    "type": "项目记忆卡",
                    "domain": "项目",
                    "project": project_slug,
                    "tags": ["原子记忆", kind],
                    "updated": today.isoformat(),
                    "id": disputed_id,
                    "stable_id": card_id,
                    "stable_key": stable_key,
                    "kind": kind,
                    "status": "disputed",
                    "effective_from": today.isoformat(),
                    "supersedes": [],
                    "conflicts_with": [card_id],
                    "source_receipt": task_id,
                    "evidence_refs": evidence_refs,
                    "destination": destination,
                    "last_verified": today.isoformat(),
                    "confidence": "review_required",
                    "content_hash": digest,
                    "summary": summary,
                }
                write_text_atomic(disputed_path, render_card(frontmatter, summary))
            results.append({"id": disputed_id, "action": "disputed", "status": "disputed"})
            continue

        supersedes_ids: list[str] = []
        for prior_key in string_list(candidate.get("supersedes")):
            prior_id = active_keys.get(normalized_key(prior_key))
            prior_kind = str(existing[prior_id][1].get("kind") or "") if prior_id else ""
            if prior_id and prior_kind == kind and prior_id not in supersedes_ids:
                supersedes_ids.append(prior_id)

        frontmatter = {
            "title": summary,
            "type": "项目记忆卡",
            "domain": "项目",
            "project": project_slug,
            "tags": ["原子记忆", kind],
            "updated": today.isoformat(),
            "id": card_id,
            "stable_key": stable_key,
            "kind": kind,
            "status": status,
            "effective_from": today.isoformat(),
            "supersedes": supersedes_ids,
            "source_receipt": task_id,
            "evidence_refs": evidence_refs,
            "destination": destination,
            "review_reasons": review_reasons,
            "last_verified": today.isoformat(),
            "confidence": "verified" if status == "active" else "review_required",
            "content_hash": digest,
            "summary": summary,
        }
        card_path = memory_dir / f"{card_id}.md"
        write_text_atomic(card_path, render_card(frontmatter, summary))
        existing[card_id] = (card_path, frontmatter, summary)
        if status == "active":
            active_keys[stable_key] = card_id
            for prior_id in supersedes_ids:
                prior_path, prior_frontmatter, prior_body = existing[prior_id]
                prior_frontmatter = dict(prior_frontmatter)
                prior_frontmatter["status"] = "superseded"
                prior_frontmatter["superseded_by"] = card_id
                write_text_atomic(prior_path, render_markdown(prior_frontmatter, prior_body))
                existing[prior_id] = (prior_path, prior_frontmatter, prior_body)
        results.append({"id": card_id, "action": "created", "status": status})

    return {
        "status": "compiled",
        "reasons": [],
        "cards": results,
        "memory_dir": f"20_projects/active/{project_slug}/memory",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile bounded current-memory projections.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    try:
        context = json.loads((repo_root / "wiki.context.json").read_text(encoding="utf-8"))
        wiki_root = Path(str(context["wiki_root"])).expanduser().resolve()
        project_slug = str(context["project_slug"])
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        raise SystemExit(f"invalid wiki.context.json: {exc}")
    report = compile_projections(
        wiki_root=wiki_root,
        project_slug=project_slug,
        dry_run=args.dry_run,
    )
    printable = {**report, "pages": [{key: value for key, value in page.items() if key != "content"} for page in report["pages"]]}
    print(json.dumps(printable, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
