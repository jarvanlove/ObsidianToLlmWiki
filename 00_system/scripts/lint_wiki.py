from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

from schema_lib import load_schema_registry, page_link, validate_page_schema
from wiki_lib import SCRIPT_DIR, VAULT_ROOT, append_log, iter_markdown_files, load_page, parse_date, write_text

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)")


def resolve_link(target: str, page_map: dict[str, Path], stem_map: dict[str, list[Path]]) -> Path | None:
    normalized = target.strip().replace("\\", "/").removesuffix(".md")
    if normalized in page_map:
        return page_map[normalized]
    stem = Path(normalized).name
    matches = stem_map.get(stem, [])
    if len(matches) == 1:
        return matches[0]
    return None


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
        or rel_path.startswith("40_outputs/analyses/知识库体检-")
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="执行知识库体检，检查结构与治理问题。")
    parser.add_argument("--stale-days", type=int, default=45, help="超过多少天未更新则视为过期")
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
    duplicate_titles: dict[str, list[dict[str, object]]] = defaultdict(list)

    for rel_path, path in page_map.items():
        stem_map[Path(rel_path).name].append(path)

    for page in pages:
        matches = WIKILINK_RE.findall(str(page["body"]))
        for match in matches:
            resolved = resolve_link(match, page_map, stem_map)
            if resolved is not None:
                incoming[resolved].add(page["path"])
            else:
                dead_links[page["path"]].append(match)

        for error in validate_page_schema(page, schema_registry):
            schema_errors[page["path"]].append(error)

        title = str(page["title"]).strip()
        rel_path = str(page["rel_path"])
        if title and not should_skip_orphan(rel_path):
            duplicate_titles[title].append(page)

    today = date.today()
    orphans: list[dict[str, object]] = []
    stale: list[dict[str, object]] = []
    unfiled_sources: list[dict[str, object]] = []
    pending_media_sources: list[dict[str, object]] = []

    for page in pages:
        rel_path = str(page["rel_path"])
        if should_skip_orphan(rel_path):
            continue
        if page["path"] not in incoming:
            orphans.append(page)

        frontmatter = page["frontmatter"]
        if isinstance(frontmatter, dict):
            updated = parse_date(str(frontmatter.get("updated") or ""))
            if updated is not None and (today - updated).days > args.stale_days:
                stale.append(page)

            note_type = str(frontmatter.get("type") or "").strip()
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
    duplicate_title_count = len(duplicate_groups)

    report_path = VAULT_ROOT / "40_outputs" / "analyses" / f"知识库体检-{today.isoformat()}.md"
    lines = [
        f"# 知识库体检 {today.isoformat()}",
        "",
        f"- 孤儿页面: {len(orphans)}",
        f"- 过期页面: {len(stale)}",
        f"- Schema 问题: {schema_issue_count}",
        f"- 死链接: {dead_link_count}",
        f"- 重复标题组: {duplicate_title_count}",
        f"- 未沉淀来源: {len(unfiled_sources)}",
        f"- 待处理媒体来源: {len(pending_media_sources)}",
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
