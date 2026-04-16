from __future__ import annotations

import json
from pathlib import Path

from wiki_lib import VAULT_ROOT, parse_date


SCHEMA_PATH = VAULT_ROOT / "00_system" / "registry" / "page_schemas.json"
EXEMPT_SCHEMA_PATHS = {
    "AGENTS.md",
    "CLAUDE.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "Home.md",
    "LICENSE",
    "README.md",
    "README-zh.md",
    "SECURITY.md",
    "index.md",
    "log.md",
    "会话启动页.md",
    "使用手册.md",
}


def load_schema_registry() -> dict[str, object]:
    if not SCHEMA_PATH.exists():
        return {"default_required": [], "type_rules": {}}
    try:
        return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"default_required": [], "type_rules": {}}


def page_requires_schema(rel_path: str) -> bool:
    return (
        rel_path not in EXEMPT_SCHEMA_PATHS
        and not rel_path.endswith("/索引.md")
        and not rel_path.endswith("/关系索引.md")
        and not rel_path.startswith("40_outputs/analyses/知识库体检-")
    )


def validate_page_schema(page: dict[str, object], registry: dict[str, object]) -> list[str]:
    rel_path = str(page["rel_path"])
    if not page_requires_schema(rel_path):
        return []

    frontmatter = page.get("frontmatter", {})
    if not isinstance(frontmatter, dict) or not frontmatter:
        return ["缺少 frontmatter。"]

    errors: list[str] = []
    note_type = str(frontmatter.get("type") or "").strip()
    default_required = [str(item) for item in registry.get("default_required", []) if str(item).strip()]
    type_rules = registry.get("type_rules", {})
    rule = type_rules.get(note_type, {}) if isinstance(type_rules, dict) else {}
    required_fields = default_required + [str(item) for item in rule.get("required", []) if str(item).strip()]

    for field in required_fields:
        value = frontmatter.get(field)
        if value is None:
            errors.append(f"缺少字段 `{field}`。")
            continue
        if isinstance(value, str) and not value.strip():
            errors.append(f"字段 `{field}` 为空。")
        if isinstance(value, list) and not value:
            errors.append(f"字段 `{field}` 为空列表。")

    allowed_domains = [str(item) for item in rule.get("domain", []) if str(item).strip()]
    domain = str(frontmatter.get("domain") or "").strip()
    if allowed_domains and domain not in allowed_domains:
        errors.append(f"`domain` 非法，当前为 `{domain}`，允许值: {', '.join(allowed_domains)}。")

    updated = frontmatter.get("updated")
    updated_text = str(updated).strip() if updated is not None else ""
    if updated_text and parse_date(updated_text) is None:
        errors.append(f"`updated` 不是 ISO 日期: `{updated_text}`。")

    tags = frontmatter.get("tags")
    if tags is not None and not isinstance(tags, list):
        errors.append("`tags` 必须是 YAML 列表。")

    if note_type == "来源":
        ingest_status = str(frontmatter.get("ingest_status") or "").strip()
        if ingest_status and ingest_status not in {"已登记", "已解析", "已总结", "已沉淀", "已提升", "已归档"}:
            errors.append(f"`ingest_status` 非法: `{ingest_status}`。")
        derived_pages = frontmatter.get("derived_pages")
        if derived_pages is not None and not isinstance(derived_pages, list):
            errors.append("`derived_pages` 必须是 YAML 列表。")
        recommended_targets = frontmatter.get("recommended_targets")
        if recommended_targets is not None and not isinstance(recommended_targets, list):
            errors.append("`recommended_targets` 必须是 YAML 列表。")
        review_due = frontmatter.get("review_due")
        review_due_text = str(review_due).strip() if review_due is not None else ""
        if review_due_text and parse_date(review_due_text) is None:
            errors.append(f"`review_due` 不是 ISO 日期: `{review_due_text}`。")

    project = str(frontmatter.get("project") or "").strip()
    if domain == "项目" and not project:
        errors.append("项目页必须填写 `project`。")

    if note_type == "项目":
        for field in ("depends_on", "reuses", "produces", "related_to"):
            value = frontmatter.get(field)
            if value is not None and not isinstance(value, list):
                errors.append(f"`{field}` 必须是 YAML 列表。")

    if note_type == "反思":
        candidate_score = frontmatter.get("candidate_score")
        if candidate_score is not None:
            try:
                int(candidate_score)
            except (TypeError, ValueError):
                errors.append("`candidate_score` 必须是整数。")
        for field in ("candidate_signature", "candidate_source", "promoted_to"):
            value = frontmatter.get(field)
            if value is not None and not isinstance(value, str):
                errors.append(f"`{field}` 必须是字符串。")

    return errors


def page_link(path_or_rel: Path | str, title: str) -> str:
    rel = Path(path_or_rel).with_suffix("").as_posix()
    return f"[[{rel}|{title}]]"
