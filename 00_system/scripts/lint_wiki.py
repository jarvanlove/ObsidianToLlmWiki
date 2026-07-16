from __future__ import annotations

import argparse
import posixpath
import re
import subprocess
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

from schema_lib import load_schema_registry, page_link, validate_page_schema
from wiki_lib import (
    SCRIPT_DIR,
    VAULT_ROOT,
    append_log,
    iter_markdown_files,
    load_page,
    parse_date,
    resolve_wikilink,
    strip_fenced_code_blocks,
    write_text,
)

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)")
SECTION_NOTE_REQUIRED_HEADINGS = (
    "## 本节主题",
    "## 关键概念",
    "## 关键事实",
    "## 操作步骤或流程",
    "## 原文摘录",
    "## 待追问问题",
    "## 沉淀候选",
)
INGEST_QUALITY_FIELDS = (
    "quality_status",
    "quality_total_units",
    "quality_extracted_units",
    "quality_empty_units",
    "quality_extracted_chars",
    "quality_unit_coverage",
    "quality_garbled_ratio",
    "quality_fragmented_cjk_ratio",
    "needs_ocr",
    "quality_warnings",
)


def should_skip_orphan(rel_path: str) -> bool:
    return (
        rel_path
        in {
            "Home.md",
            "index.md",
            "log.md",
            "AGENTS.md",
            "CLAUDE.md",
            "README.md",
            "README-zh.md",
            "CHANGELOG.md",
            "CONTRIBUTING.md",
            "SECURITY.md",
        }
        or rel_path.endswith("/索引.md")
        or rel_path.endswith("/关系索引.md")
        or rel_path.startswith("40_outputs/analyses/知识库体检-")
        or rel_path == "40_outputs/学习候选审批视图.md"
    )


def should_check_orphan(page: dict[str, object]) -> bool:
    rel_path = str(page["rel_path"])
    if should_skip_orphan(rel_path) or rel_path.startswith("20_projects/archive/"):
        return False
    frontmatter = page.get("frontmatter")
    if not isinstance(frontmatter, dict):
        return True
    status = str(frontmatter.get("status") or "").strip()
    return status not in {"历史", "归档", "已归档", "已收录"}


def should_skip_link_source(rel_path: str) -> bool:
    return rel_path.startswith("40_outputs/analyses/知识库体检-")


def should_check_links(page: dict[str, object]) -> bool:
    rel_path = str(page["rel_path"])
    if should_skip_link_source(rel_path) or rel_path.startswith("20_projects/archive/"):
        return False
    frontmatter = page.get("frontmatter")
    if not isinstance(frontmatter, dict):
        return True
    status = str(frontmatter.get("status") or "").strip()
    return status not in {"历史", "归档", "已归档", "已收录"}


def direct_wikilink_target_exists(
    target: str,
    source_rel_path: str,
    *,
    vault_root: Path = VAULT_ROOT,
) -> bool:
    normalized = target.strip().replace("\\", "/").removesuffix(".md").lstrip("/")
    source_parent = posixpath.dirname(source_rel_path.replace("\\", "/"))
    candidates = {normalized, posixpath.normpath(posixpath.join(source_parent, normalized))}
    for candidate in candidates:
        if not candidate or candidate == ".." or candidate.startswith("../"):
            continue
        if (vault_root / f"{candidate}.md").is_file():
            return True
    return False


def should_check_stale(page: dict[str, object]) -> bool:
    rel_path = str(page["rel_path"])
    if (
        rel_path.startswith("20_projects/archive/")
        or "/sources/" in rel_path
        or "/source-notes/" in rel_path
    ):
        return False
    frontmatter = page.get("frontmatter")
    if not isinstance(frontmatter, dict):
        return False
    status = str(frontmatter.get("status") or "").strip()
    return status in {"活跃", "常青", "进行中", "待处理", "待验证"}


def page_freshness_date(page: dict[str, object]) -> date | None:
    frontmatter = page.get("frontmatter")
    if not isinstance(frontmatter, dict):
        return None
    reviewed = parse_date(str(frontmatter.get("reviewed") or ""))
    if reviewed is not None:
        return reviewed
    return parse_date(str(frontmatter.get("updated") or ""))


def section_requires_promotion_review(
    frontmatter: dict[str, object],
    *,
    today: date,
    backlog_days: int,
) -> bool:
    updated = parse_date(str(frontmatter.get("updated") or ""))
    status = str(frontmatter.get("status") or "").strip()
    has_targets = bool(list_items(frontmatter.get("recommended_targets")))
    return bool(
        updated is not None
        and status == "已生成"
        and has_targets
        and (today - updated).days > backlog_days
    )


def extract_section(body: str, heading: str) -> str:
    start = body.find(heading)
    if start == -1:
        return ""
    start += len(heading)
    next_heading = body.find("\n## ", start)
    if next_heading == -1:
        return body[start:].strip()
    return body[start:next_heading].strip()


def list_items(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def check_structured_ingest_quality(page: dict[str, object]) -> list[str]:
    frontmatter = page["frontmatter"]
    if not isinstance(frontmatter, dict):
        return []
    note_type = str(frontmatter.get("type") or "").strip()
    body = str(page["body"])
    errors: list[str] = []

    if note_type == "来源":
        extract_mode = str(frontmatter.get("extract_mode") or "").strip()
        media_type = str(frontmatter.get("media_type") or "").strip()
        if media_type == "document" and extract_mode in {"text", "docx", "pptx", "pdf"}:
            quality_version = frontmatter.get("ingest_quality_version")
            quality_status = str(frontmatter.get("quality_status") or "").strip()
            if quality_version:
                for field in INGEST_QUALITY_FIELDS:
                    if field not in frontmatter:
                        errors.append(f"quality-gated source is missing field: {field}")
                if quality_status not in {"pass", "review", "blocked"}:
                    errors.append("quality-gated source has an invalid quality_status")
            derived_pages = list_items(frontmatter.get("derived_pages"))
            if quality_status == "blocked":
                if derived_pages:
                    errors.append("blocked source must not create document derivatives")
            elif not any(path.endswith("-document-map.md") for path in derived_pages):
                errors.append("structured document source is missing a document map in derived_pages")
            if quality_status != "blocked" and not any("-sections/" in path for path in derived_pages):
                errors.append("structured document source is missing section notes in derived_pages")

    if note_type == "文档地图":
        if frontmatter.get("ingest_quality_version"):
            for field in INGEST_QUALITY_FIELDS:
                if field not in frontmatter:
                    errors.append(f"quality-gated document map is missing field: {field}")
        derived_sections = list_items(frontmatter.get("derived_sections"))
        if not derived_sections:
            errors.append("document map has no derived_sections")
        try:
            section_count = int(str(frontmatter.get("section_count") or "0"))
        except ValueError:
            section_count = 0
        if section_count <= 0:
            errors.append("document map section_count must be greater than 0")
        elif derived_sections and len(derived_sections) != section_count:
            errors.append("document map section_count does not match derived_sections length")

    if note_type == "章节笔记":
        for heading in SECTION_NOTE_REQUIRED_HEADINGS:
            if heading not in body:
                errors.append(f"section note is missing heading: {heading}")
        source_refs = list_items(frontmatter.get("source_refs"))
        if not source_refs:
            errors.append("section note has no source_refs")
        try:
            excerpt_limit = int(str(frontmatter.get("excerpt_limit_chars") or "0"))
        except ValueError:
            excerpt_limit = 0
        excerpt = extract_section(body, "## 原文摘录")
        excerpt = re.sub(r"^- 摘录限制:.*$", "", excerpt, flags=re.MULTILINE).strip()
        if excerpt_limit <= 0:
            errors.append("section note excerpt_limit_chars must be greater than 0")
        elif len(excerpt) > excerpt_limit + 120:
            errors.append("section note excerpt appears to exceed excerpt_limit_chars")
        recommended_targets = list_items(frontmatter.get("recommended_targets"))
        if not recommended_targets:
            errors.append("section note has no recommended_targets")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="执行知识库体检，检查结构与治理问题。")
    parser.add_argument("--stale-days", type=int, default=45, help="超过多少天未更新则视为过期")
    parser.add_argument("--section-backlog-days", type=int, default=14, help="章节笔记超过多少天未沉淀则视为积压")
    args = parser.parse_args()

    subprocess.run([sys.executable, str(SCRIPT_DIR / "sync_source_notes.py")], check=True)
    subprocess.run([sys.executable, str(SCRIPT_DIR / "recommend_source_promotions.py")], check=True)
    subprocess.run([sys.executable, str(SCRIPT_DIR / "sync_project_relations.py")], check=True)
    subprocess.run([sys.executable, str(SCRIPT_DIR / "sync_personal_relations.py")], check=True)
    subprocess.run([sys.executable, str(SCRIPT_DIR / "rebuild_indexes.py")], check=True)

    pages = [load_page(path) for path in iter_markdown_files()]
    page_map = {str(page["rel_path"]).removesuffix(".md"): page["path"] for page in pages}
    stem_map: dict[str, list[Path]] = defaultdict(list)
    incoming: dict[Path, set[Path]] = defaultdict(set)
    dead_links: dict[Path, list[str]] = defaultdict(list)
    schema_registry = load_schema_registry()
    schema_errors: dict[Path, list[str]] = defaultdict(list)
    structured_ingest_errors: dict[Path, list[str]] = defaultdict(list)
    duplicate_titles: dict[str, list[dict[str, object]]] = defaultdict(list)

    for rel_path, path in page_map.items():
        stem_map[Path(rel_path).name].append(path)

    for page in pages:
        source_rel_path = str(page["rel_path"])
        if not should_check_links(page):
            continue
        matches = WIKILINK_RE.findall(strip_fenced_code_blocks(str(page["body"])))
        for match in matches:
            resolved = resolve_wikilink(match, source_rel_path, page_map, stem_map)
            if resolved is not None:
                incoming[resolved].add(page["path"])
            elif not direct_wikilink_target_exists(match, source_rel_path):
                dead_links[page["path"]].append(match)

        for error in validate_page_schema(page, schema_registry):
            schema_errors[page["path"]].append(error)
        for error in check_structured_ingest_quality(page):
            structured_ingest_errors[page["path"]].append(error)

        title = str(page["title"]).strip()
        rel_path = str(page["rel_path"])
        if title and should_check_orphan(page):
            duplicate_titles[title].append(page)

    today = date.today()
    orphans: list[dict[str, object]] = []
    stale: list[dict[str, object]] = []
    unfiled_sources: list[dict[str, object]] = []
    pending_media_sources: list[dict[str, object]] = []
    section_promotion_backlog: list[dict[str, object]] = []

    for page in pages:
        rel_path = str(page["rel_path"])
        if not should_check_orphan(page):
            continue
        if page["path"] not in incoming:
            orphans.append(page)

        frontmatter = page["frontmatter"]
        if isinstance(frontmatter, dict):
            freshness_date = page_freshness_date(page)
            if (
                should_check_stale(page)
                and freshness_date is not None
                and (today - freshness_date).days > args.stale_days
            ):
                stale.append(page)

            note_type = str(frontmatter.get("type") or "").strip()
            if note_type == "章节笔记" and section_requires_promotion_review(
                frontmatter,
                today=today,
                backlog_days=args.section_backlog_days,
            ):
                section_promotion_backlog.append(page)
            if note_type == "来源":
                media_type = str(frontmatter.get("media_type") or "").strip()
                parse_status = str(frontmatter.get("parse_status") or "").strip()
                if media_type in {"image", "audio", "video"} and parse_status in {"待处理", "处理中", "失败"}:
                    pending_media_sources.append(page)
                derived_pages = frontmatter.get("derived_pages")
                if isinstance(derived_pages, list) and derived_pages:
                    continue
                ingest_status = str(frontmatter.get("ingest_status") or "").strip()
                if ingest_status in {"已沉淀", "已提升", "已归档"}:
                    continue
                incoming_paths = incoming.get(page["path"], set())
                has_derived_reference = False
                for source_page in incoming_paths:
                    source_rel_path = source_page.relative_to(VAULT_ROOT).as_posix()
                    source_meta = next((candidate for candidate in pages if candidate["path"] == source_page), None)
                    source_type = ""
                    if source_meta and isinstance(source_meta["frontmatter"], dict):
                        source_type = str(source_meta["frontmatter"].get("type") or "").strip()
                    if source_rel_path.endswith("来源.md"):
                        continue
                    if source_type != "来源":
                        has_derived_reference = True
                        break
                if not has_derived_reference:
                    unfiled_sources.append(page)

    duplicate_groups = {
        title: items for title, items in duplicate_titles.items() if len(items) > 1
    }
    dead_link_count = sum(len(items) for items in dead_links.values())
    schema_issue_count = sum(len(items) for items in schema_errors.values())
    structured_ingest_issue_count = sum(len(items) for items in structured_ingest_errors.values())
    duplicate_title_count = len(duplicate_groups)

    report_path = VAULT_ROOT / "40_outputs" / "analyses" / f"知识库体检-{today.isoformat()}.md"
    lines = [
        f"# 知识库体检 {today.isoformat()}",
        "",
        f"- 孤儿页面: {len(orphans)}",
        f"- 过期页面: {len(stale)}",
        f"- Schema 问题: {schema_issue_count}",
        f"- 结构化摄入问题: {structured_ingest_issue_count}",
        f"- 死链接: {dead_link_count}",
        f"- 重复标题组: {duplicate_title_count}",
        f"- 未沉淀来源: {len(unfiled_sources)}",
        f"- 待处理媒体来源: {len(pending_media_sources)}",
        f"- 章节沉淀积压: {len(section_promotion_backlog)}",
        "",
        "## 孤儿页面",
        "",
    ]
    if orphans:
        for page in sorted(orphans, key=lambda item: str(item["rel_path"])):
            lines.append(f"- [[{Path(str(page['rel_path'])).with_suffix('').as_posix()}|{page['title']}]]")
    else:
        lines.append("- 无。")

    lines.extend(["", "## 过期页面", ""])
    if stale:
        for page in sorted(stale, key=lambda item: str(item["rel_path"])):
            lines.append(f"- [[{Path(str(page['rel_path'])).with_suffix('').as_posix()}|{page['title']}]]")
    else:
        lines.append("- 无。")

    lines.extend(["", "## Schema 问题", ""])
    if schema_errors:
        for page in sorted((page for page in pages if page["path"] in schema_errors), key=lambda item: str(item["rel_path"])):
            lines.append(f"- {page_link(str(page['rel_path']), str(page['title']))}")
            for error in schema_errors[page["path"]]:
                lines.append(f"  - {error}")
    else:
        lines.append("- 无。")

    lines.extend(["", "## 结构化摄入问题", ""])
    if structured_ingest_errors:
        for page in sorted((page for page in pages if page["path"] in structured_ingest_errors), key=lambda item: str(item["rel_path"])):
            lines.append(f"- {page_link(str(page['rel_path']), str(page['title']))}")
            for error in structured_ingest_errors[page["path"]]:
                lines.append(f"  - {error}")
    else:
        lines.append("- 无。")

    lines.extend(["", "## 死链接", ""])
    if dead_links:
        for page in sorted((page for page in pages if page["path"] in dead_links), key=lambda item: str(item["rel_path"])):
            targets = ", ".join(f"`{target}`" for target in sorted(set(dead_links[page["path"]])))
            lines.append(f"- {page_link(str(page['rel_path']), str(page['title']))}: {targets}")
    else:
        lines.append("- 无。")

    lines.extend(["", "## 重复标题", ""])
    if duplicate_groups:
        for title, items in sorted(duplicate_groups.items(), key=lambda item: item[0]):
            links = "；".join(page_link(str(page["rel_path"]), str(page["rel_path"])) for page in sorted(items, key=lambda entry: str(entry["rel_path"])))
            lines.append(f"- `{title}`: {links}")
    else:
        lines.append("- 无。")

    lines.extend(["", "## 未沉淀来源", ""])
    if unfiled_sources:
        for page in sorted(unfiled_sources, key=lambda item: str(item["rel_path"])):
            lines.append(f"- {page_link(str(page['rel_path']), str(page['title']))}")
    else:
        lines.append("- 无。")

    lines.extend(["", "## 章节沉淀积压", ""])
    if section_promotion_backlog:
        for page in sorted(section_promotion_backlog, key=lambda item: str(item["rel_path"])):
            frontmatter = page["frontmatter"]
            targets = list_items(frontmatter.get("recommended_targets")) if isinstance(frontmatter, dict) else []
            lines.append(f"- {page_link(str(page['rel_path']), str(page['title']))}: {', '.join(f'`{target}`' for target in targets)}")
    else:
        lines.append("- 无。")

    lines.extend(["", "## 待处理媒体来源", ""])
    if pending_media_sources:
        for page in sorted(pending_media_sources, key=lambda item: str(item["rel_path"])):
            frontmatter = page["frontmatter"]
            media_type = str(frontmatter.get("media_type") or "").strip()
            parse_status = str(frontmatter.get("parse_status") or "").strip()
            lines.append(f"- {page_link(str(page['rel_path']), str(page['title']))}: `{media_type}` / `{parse_status}`")
    else:
        lines.append("- 无。")

    write_text(report_path, "\n".join(lines))
    append_log("体检", "知识库体检", f"报告已写入 {report_path.relative_to(VAULT_ROOT).as_posix()}")
    print(report_path)


if __name__ == "__main__":
    main()
