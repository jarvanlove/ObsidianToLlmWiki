from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

from wiki_lib import SCRIPT_DIR, append_log, iter_markdown_files, load_page, slugify, update_page_frontmatter

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:\|[^\]]+)?\]\]")
SECTION_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)
SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？.!?])")
BUILDS_ON_HEADINGS = {"来源", "关联实体", "基础概念", "前置知识", "建立在", "依赖"}
BUILDS_ON_HINTS = {"基于", "建立在", "依赖", "前提", "来源", "关联实体"}
GENERIC_TAGS = {"个人", "知识", "综述", "分析", "实体", "概念", "领域", "方法", "经验"}


def split_sections(body: str) -> dict[str, str]:
    matches = list(SECTION_RE.finditer(body))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        heading = match.group(1).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        sections[heading] = body[start:end].strip()
    return sections


def extract_wikilinks(text: str) -> list[str]:
    return [match.strip() for match in WIKILINK_RE.findall(text)]


def normalize_target(target: str) -> str:
    return target.strip().replace("\\", "/").removesuffix(".md")


def sentence_for_target(text: str, target: str) -> str:
    sentences = SENTENCE_SPLIT_RE.split(text)
    for sentence in sentences:
        if target in sentence:
            return sentence
    return text


def personal_pages() -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for path in iter_markdown_files():
        page = load_page(path)
        frontmatter = page["frontmatter"]
        if not isinstance(frontmatter, dict):
            continue
        rel_path = str(page["rel_path"])
        domain = str(frontmatter.get("domain") or "").strip()
        if domain == "个人" and rel_path.startswith("10_personal/") and not rel_path.endswith("/索引.md"):
            result.append(page)
    return result


def personal_page_maps(pages: list[dict[str, object]]) -> tuple[dict[str, dict[str, object]], dict[str, list[dict[str, object]]]]:
    rel_map: dict[str, dict[str, object]] = {}
    stem_map: dict[str, list[dict[str, object]]] = {}
    for page in pages:
        rel_key = str(page["rel_path"]).removesuffix(".md")
        rel_map[rel_key] = page
        stem = Path(rel_key).name
        stem_map.setdefault(stem, []).append(page)
    return rel_map, stem_map


def resolve_personal_target(
    target: str,
    rel_map: dict[str, dict[str, object]],
    stem_map: dict[str, list[dict[str, object]]],
) -> dict[str, object] | None:
    normalized = normalize_target(target)
    if normalized in rel_map:
        return rel_map[normalized]
    stem = Path(normalized).name
    matches = stem_map.get(stem, [])
    if len(matches) == 1:
        return matches[0]
    return None


def infer_relation(
    *,
    heading: str,
    sentence: str,
    source_page: dict[str, object],
    target_page: dict[str, object],
) -> str:
    heading_text = heading.strip()
    sentence_text = sentence.strip()
    source_frontmatter = source_page["frontmatter"]
    target_frontmatter = target_page["frontmatter"]
    source_type = str(source_frontmatter.get("type") or "").strip() if isinstance(source_frontmatter, dict) else ""
    target_type = str(target_frontmatter.get("type") or "").strip() if isinstance(target_frontmatter, dict) else ""

    if heading_text in BUILDS_ON_HEADINGS:
        return "builds_on"
    if any(keyword in sentence_text for keyword in BUILDS_ON_HINTS):
        return "builds_on"
    if source_type in {"综述", "分析"} and target_type in {"实体", "概念", "领域"}:
        return "builds_on"
    return "related_to"


def normalized_tag_set(page: dict[str, object]) -> set[str]:
    tags = {
        str(tag).strip().lower()
        for tag in page["tags"]
        if str(tag).strip() and str(tag).strip().lower() not in GENERIC_TAGS
    }
    return tags


def infer_relations_for_page(
    page: dict[str, object],
    personal_pages: list[dict[str, object]],
    rel_map: dict[str, dict[str, object]],
    stem_map: dict[str, list[dict[str, object]]],
) -> tuple[list[str], list[str]]:
    related_to: set[str] = set()
    builds_on: set[str] = set()
    body = str(page["body"])
    sections = split_sections(body)
    source_rel = str(page["rel_path"]).removesuffix(".md")
    source_frontmatter = page["frontmatter"]
    page_project = str(source_frontmatter.get("project") or "").strip() if isinstance(source_frontmatter, dict) else ""

    if sections:
        for heading, text in sections.items():
            for raw_target in extract_wikilinks(text):
                target_page = resolve_personal_target(raw_target, rel_map, stem_map)
                if target_page is None:
                    continue
                target_rel = str(target_page["rel_path"]).removesuffix(".md")
                if target_rel == source_rel:
                    continue
                sentence = sentence_for_target(text, raw_target)
                relation = infer_relation(
                    heading=heading,
                    sentence=sentence,
                    source_page=page,
                    target_page=target_page,
                )
                if relation == "builds_on":
                    builds_on.add(f"[[{target_rel}|{target_page['title']}]]")
                else:
                    related_to.add(f"[[{target_rel}|{target_page['title']}]]")
    else:
        for raw_target in extract_wikilinks(body):
            target_page = resolve_personal_target(raw_target, rel_map, stem_map)
            if target_page is None:
                continue
            target_rel = str(target_page["rel_path"]).removesuffix(".md")
            if target_rel == source_rel:
                continue
            sentence = sentence_for_target(body, raw_target)
            relation = infer_relation(
                heading="",
                sentence=sentence,
                source_page=page,
                target_page=target_page,
            )
            if relation == "builds_on":
                builds_on.add(f"[[{target_rel}|{target_page['title']}]]")
            else:
                related_to.add(f"[[{target_rel}|{target_page['title']}]]")

    current_related = source_frontmatter.get("related_to") if isinstance(source_frontmatter.get("related_to"), list) else []
    current_builds_on = source_frontmatter.get("builds_on") if isinstance(source_frontmatter.get("builds_on"), list) else []
    for item in current_related:
        if str(item).strip():
            related_to.add(str(item).strip())
    for item in current_builds_on:
        if str(item).strip():
            builds_on.add(str(item).strip())

    source_tags = normalized_tag_set(page)
    if len(related_to) < 3 and source_tags:
        for other_page in personal_pages:
            other_rel = str(other_page["rel_path"]).removesuffix(".md")
            if other_rel == source_rel:
                continue
            other_tags = normalized_tag_set(other_page)
            overlap = source_tags & other_tags
            if len(overlap) >= 2:
                related_to.add(f"[[{other_rel}|{other_page['title']}]]")

    if len(related_to) < 3 and page_project:
        for other_page in personal_pages:
            other_rel = str(other_page["rel_path"]).removesuffix(".md")
            if other_rel == source_rel:
                continue
            other_frontmatter = other_page["frontmatter"]
            other_project = str(other_frontmatter.get("project") or "").strip() if isinstance(other_frontmatter, dict) else ""
            if other_project and other_project == page_project:
                related_to.add(f"[[{other_rel}|{other_page['title']}]]")

    return sorted(related_to), sorted(builds_on)


def sync_one_page(
    page: dict[str, object],
    all_personal_pages: list[dict[str, object]],
    rel_map: dict[str, dict[str, object]],
    stem_map: dict[str, list[dict[str, object]]],
) -> bool:
    frontmatter = page["frontmatter"]
    if not isinstance(frontmatter, dict):
        return False

    next_related, next_builds_on = infer_relations_for_page(page, all_personal_pages, rel_map, stem_map)
    current_related = [str(item) for item in frontmatter.get("related_to", [])] if isinstance(frontmatter.get("related_to"), list) else []
    current_builds_on = [str(item) for item in frontmatter.get("builds_on", [])] if isinstance(frontmatter.get("builds_on"), list) else []

    updates: dict[str, object] = {}
    if current_related != next_related:
        updates["related_to"] = next_related
    if current_builds_on != next_builds_on:
        updates["builds_on"] = next_builds_on

    if not updates:
        return False

    update_page_frontmatter(Path(str(page["path"])), updates)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="把个人知识页中的链接、标签和来源项目同步为关系字段。")
    parser.add_argument("--rebuild", action="store_true", help="同步后重建索引")
    args = parser.parse_args()

    pages = personal_pages()
    rel_map, stem_map = personal_page_maps(pages)

    updated = 0
    for page in pages:
        if sync_one_page(page, pages, rel_map, stem_map):
            updated += 1

    if updated:
        append_log("更新", "同步个人关系", f"已更新 {updated} 个个人知识页的关系字段")

    if args.rebuild:
        subprocess.run([sys.executable, str(SCRIPT_DIR / "rebuild_indexes.py")], check=True)

    print(f"updated={updated}")


if __name__ == "__main__":
    main()
