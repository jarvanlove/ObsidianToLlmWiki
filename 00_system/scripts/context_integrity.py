from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path

from wiki_lib import (
    FrontmatterError,
    PrivatePolicyError,
    ai_access_exclusion_reason,
    load_private_policy,
    parse_frontmatter,
)


SCRIPT_DIR = Path(__file__).resolve().parent
SOURCE_ROOT = SCRIPT_DIR.parent.parent
POLICY_PATH = SOURCE_ROOT / "00_system" / "registry" / "memory_policy.json"
SCHEMA_PATH = SOURCE_ROOT / "00_system" / "registry" / "page_schemas.json"
TRUST_STATES = ("trusted", "review_required", "degraded", "quarantined")
SEVERITY = {state: index for index, state in enumerate(TRUST_STATES)}


def _load_json_object(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} root value must be an object")
    return payload


def load_memory_policy() -> dict[str, object]:
    policy = _load_json_object(POLICY_PATH)
    if policy.get("schema_version") != 1:
        raise ValueError("memory_policy.json requires schema_version=1")
    states = policy.get("allowed_states")
    if states != list(TRUST_STATES):
        raise ValueError("memory_policy.json allowed_states do not match the runtime contract")

    schema = _load_json_object(SCHEMA_PATH)
    merged = dict(policy)
    merged["required_fields"] = schema.get("default_required", [])
    merged["type_rules"] = schema.get("type_rules", {})
    if not merged.get("provenance_fields"):
        merged["provenance_fields"] = schema.get("provenance_fields", [])
    return merged


def _date_value(value: object) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


def _has_value(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple, set)):
        return bool(value)
    return True


def _result(path: Path, status: str, reasons: list[str], *, page_id: str = "", page_type: str = "") -> dict[str, object]:
    return {
        "path": str(path),
        "id": page_id,
        "type": page_type,
        "status": status,
        "reasons": reasons,
    }


def inspect_page(path: Path, *, policy: dict[str, object], today: date) -> dict[str, object]:
    candidate = path.expanduser().resolve()
    if not candidate.exists() or not candidate.is_file():
        return _result(candidate, "quarantined", ["missing_file"])

    vault_root_raw = str(policy.get("vault_root") or "").strip()
    private_policy = policy.get("private_policy")
    if vault_root_raw and isinstance(private_policy, dict):
        reason = ai_access_exclusion_reason(
            candidate,
            vault_root=Path(vault_root_raw),
            policy=private_policy,
        )
        if reason:
            return _result(candidate, "quarantined", ["ai_access_excluded"])

    try:
        text = candidate.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return _result(candidate, "quarantined", ["invalid_utf8"])
    except OSError:
        return _result(candidate, "quarantined", ["unreadable_file"])

    try:
        frontmatter, _body = parse_frontmatter(text)
    except FrontmatterError as exc:
        return _result(candidate, "quarantined", [exc.code])
    if not frontmatter:
        return _result(candidate, "quarantined", ["frontmatter_missing"])

    page_id = str(frontmatter.get("id") or "").strip()
    page_type = str(frontmatter.get("type") or "").strip()
    required_fields = [str(item) for item in policy.get("required_fields", []) if str(item).strip()]
    type_rules = policy.get("type_rules")
    type_rule: dict[str, object] = {}
    if isinstance(type_rules, dict):
        rule = type_rules.get(page_type)
        if isinstance(rule, dict):
            type_rule = rule
            required_fields.extend(str(item) for item in rule.get("required", []) if str(item).strip())

    reasons: list[str] = []
    for field in dict.fromkeys(required_fields):
        if not _has_value(frontmatter.get(field)):
            reasons.append(f"schema_missing:{field}")
    updated = _date_value(frontmatter.get("updated"))
    if "updated" in required_fields and _has_value(frontmatter.get("updated")) and updated is None:
        reasons.append("schema_invalid:updated")
    allowed_domains = [str(item) for item in type_rule.get("domain", []) if str(item).strip()]
    domain = str(frontmatter.get("domain") or "").strip()
    if allowed_domains and domain not in allowed_domains:
        reasons.append(f"schema_domain:{domain or '<missing>'}")
    if reasons:
        return _result(candidate, "quarantined", reasons, page_id=page_id, page_type=page_type)

    max_age_days = int(policy.get("max_age_days", policy.get("default_max_age_days", 0)) or 0)
    if updated is not None and max_age_days > 0 and (today - updated).days > max_age_days:
        reasons.append(f"stale:updated={updated.isoformat()},max_age_days={max_age_days}")

    require_provenance = bool(policy.get("require_provenance", policy.get("default_require_provenance", True)))
    provenance_fields = [str(item) for item in policy.get("provenance_fields", []) if str(item).strip()]
    if require_provenance and provenance_fields and not any(_has_value(frontmatter.get(field)) for field in provenance_fields):
        reasons.append("missing_provenance")

    card_status_trust = policy.get("card_status_trust")
    declared_status = str(frontmatter.get("status") or "").strip()
    declared_trust = card_status_trust.get(declared_status) if isinstance(card_status_trust, dict) else None
    status = str(declared_trust) if declared_trust in TRUST_STATES else "trusted"
    if any(reason.startswith("stale:") for reason in reasons):
        status = max((status, "degraded"), key=SEVERITY.get)
    elif "missing_provenance" in reasons:
        status = max((status, "review_required"), key=SEVERITY.get)
    return _result(candidate, status, reasons, page_id=page_id, page_type=page_type)


def _context_config(repo_root: Path) -> dict[str, object]:
    path = repo_root / "wiki.context.json"
    if not path.exists():
        return {}
    return _load_json_object(path)


def default_required_context(repo_root: Path, policy: dict[str, object]) -> list[dict[str, object]]:
    context = _context_config(repo_root)
    required: list[dict[str, object]] = []
    for raw in policy.get("required_project_context", []):
        if not isinstance(raw, dict):
            continue
        entry = dict(raw)
        context_key = str(entry.get("context_key") or "").strip()
        raw_path = str(context.get(context_key) or "").strip()
        if raw_path:
            entry["path"] = raw_path
        required.append(entry)
    return required


def _resolve_required_path(repo_root: Path, wiki_root: Path, entry: dict[str, object], context: dict[str, object]) -> Path:
    raw_path = str(entry.get("path") or "").strip()
    context_key = str(entry.get("context_key") or "").strip()
    if not raw_path and context_key:
        raw_path = str(context.get(context_key) or "").strip()
    if not raw_path:
        return wiki_root / f"__missing_context__/{context_key or 'required'}.md"
    candidate = Path(raw_path).expanduser()
    if candidate.is_absolute():
        return candidate
    base = repo_root if entry.get("source") == "repo" else wiki_root
    return base / candidate


def inspect_context(repo_root: Path, required: list[dict[str, object]]) -> dict[str, object]:
    resolved_repo = repo_root.expanduser().resolve()
    base_policy = load_memory_policy()
    context = _context_config(resolved_repo)
    wiki_root = Path(str(context.get("wiki_root") or resolved_repo)).expanduser().resolve()
    try:
        private_policy = load_private_policy(wiki_root)
    except PrivatePolicyError:
        private_policy = {"schema_version": 1, "ai_access": {"excluded_paths": [], "excluded_globs": []}}
        policy_error = True
    else:
        policy_error = False

    entries = required or default_required_context(resolved_repo, base_policy)
    pages: list[dict[str, object]] = []
    missing: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        path = _resolve_required_path(resolved_repo, wiki_root, entry, context)
        page_policy = dict(base_policy)
        override = entry.get("policy")
        if isinstance(override, dict):
            page_policy.update(override)
        for key in ("max_age_days", "require_provenance"):
            if key in entry:
                page_policy[key] = entry[key]
        page_policy["vault_root"] = str(wiki_root)
        page_policy["private_policy"] = private_policy
        inspected = inspect_page(path, policy=page_policy, today=date.today())
        inspected["required"] = bool(entry.get("required", True))
        pages.append(inspected)
        if inspected["reasons"] == ["missing_file"] and inspected["required"]:
            missing.append(str(path))

    ids: dict[str, list[dict[str, object]]] = {}
    for inspected in pages:
        page_id = str(inspected.get("id") or "").strip()
        if page_id:
            ids.setdefault(page_id, []).append(inspected)
    for page_id, duplicates in ids.items():
        if len(duplicates) < 2:
            continue
        for inspected in duplicates:
            inspected["status"] = "quarantined"
            inspected["reasons"] = [f"duplicate_id:{page_id}"]

    if policy_error:
        pages.append(
            {
                "path": str(wiki_root / "wiki.private.json"),
                "id": "",
                "type": "policy",
                "status": "quarantined",
                "reasons": ["private_policy_invalid"],
                "required": True,
            }
        )
    summary = {state: sum(1 for item in pages if item["status"] == state) for state in TRUST_STATES}
    status = max((str(item["status"]) for item in pages), key=SEVERITY.get, default="trusted")
    return {
        "schema_version": 1,
        "status": status,
        "reasons": [],
        "missing": missing,
        "summary": summary,
        "pages": pages,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect required AI context without modifying the project or wiki.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()
    payload = inspect_context(Path(args.repo_root), [])
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Context integrity: {payload['status']}")
        for item in payload["pages"]:
            reasons = ", ".join(item["reasons"]) or "ok"
            print(f"[{str(item['status']).upper()}] {item['path']}: {reasons}")
    if args.strict and (payload["status"] == "quarantined" or payload["missing"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
