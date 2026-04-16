from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

from wiki_lib import iter_markdown_files, load_page, obsidian_link, parse_date


def tokenize(text: str) -> list[str]:
    lowered = text.lower()
    return re.findall(r"[\u4e00-\u9fff]+|[a-z0-9]+", lowered)


def score_page(page: dict[str, object], query_terms: list[str]) -> int:
    title = str(page["title"]).lower()
    rel_path = str(page["rel_path"]).lower()
    summary = str(page["summary"]).lower()
    body = str(page["body"]).lower()
    tags = " ".join(str(tag).lower() for tag in page["tags"])

    if rel_path.startswith("40_outputs/analyses/知识库体检-"):
        return -999

    score = 0
    for term in query_terms:
        if term in title:
            score += 20
        if term in rel_path:
            score += 12
        if term in tags:
            score += 8
        if term in summary:
            score += 6
        score += body.count(term)
    if "索引.md" in rel_path:
        score -= 4
    if rel_path.startswith("00_system/"):
        score -= 5
    if rel_path.endswith("project.memory.md"):
        score += 5
    if rel_path.startswith("40_outputs/reflections/"):
        score -= 6
    if rel_path in {"agents.md", "claude.md", "readme.md", "home.md", "log.md", "index.md"}:
        score -= 12

    frontmatter = page["frontmatter"]
    if isinstance(frontmatter, dict):
        status = str(frontmatter.get("status") or "").strip()
        if status in {"活跃", "常用", "常青"}:
            score += 4
        if status in {"候选", "已归档"}:
            score -= 4

        updated = parse_date(str(frontmatter.get("updated") or ""))
        if updated is not None:
            age_days = (date.today() - updated).days
            if age_days <= 7:
                score += 5
            elif age_days <= 30:
                score += 3
            elif age_days > 180:
                score -= 2
    return score


def page_matches_filters(
    page: dict[str, object],
    *,
    project_filter: str,
    type_filter: str,
    tag_filter: str,
) -> bool:
    frontmatter = page["frontmatter"]
    if not isinstance(frontmatter, dict):
        return False

    page_project = str(frontmatter.get("project") or "").strip().lower()
    page_type = str(frontmatter.get("type") or "").strip().lower()
    page_tags = [str(tag).strip().lower() for tag in page["tags"]]

    if project_filter and project_filter not in page_project:
        return False
    if type_filter and type_filter != page_type:
        return False
    if tag_filter and tag_filter not in page_tags:
        return False
    return True


def project_index_by_slug(pages: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    for page in pages:
        rel_path = str(page["rel_path"])
        frontmatter = page["frontmatter"]
        if not isinstance(frontmatter, dict):
            continue
        if rel_path.startswith("20_projects/active/") and rel_path.endswith("/索引.md"):
            slug = str(frontmatter.get("project") or "").strip()
            if slug:
                result[slug] = page
    return result


def relation_summary(page: dict[str, object], index_by_slug: dict[str, dict[str, object]]) -> list[str]:
    frontmatter = page["frontmatter"]
    if not isinstance(frontmatter, dict):
        return []
    page_type = str(frontmatter.get("type") or "").strip()
    project_slug = str(frontmatter.get("project") or "").strip()
    if page_type == "项目":
        project_index = page
    elif project_slug and project_slug in index_by_slug:
        project_index = index_by_slug[project_slug]
    else:
        return []

    meta = project_index["frontmatter"]
    if not isinstance(meta, dict):
        return []

    lines: list[str] = []
    depends_on = meta.get("depends_on") if isinstance(meta.get("depends_on"), list) else []
    reuses = meta.get("reuses") if isinstance(meta.get("reuses"), list) else []
    produces = meta.get("produces") if isinstance(meta.get("produces"), list) else []
    related_to = meta.get("related_to") if isinstance(meta.get("related_to"), list) else []
    project_root = Path(str(project_index["path"])).parent
    memory_path = project_root / "project.memory.md"

    if depends_on:
        lines.append(f"    depends_on: {', '.join(str(item) for item in depends_on)}")
    if reuses:
        lines.append(f"    reuses: {', '.join(str(item) for item in reuses)}")
    if produces:
        lines.append(f"    produces: {', '.join(str(item) for item in produces)}")
    if related_to:
        lines.append(f"    related_to: {', '.join(str(item) for item in related_to)}")
    lines.append(f"    memory: {obsidian_link(memory_path, '运行记忆')}")
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description="对知识库 Markdown 页面执行简单词法检索。")
    parser.add_argument("query", help="搜索词")
    parser.add_argument("--limit", type=int, default=10, help="返回结果数量")
    parser.add_argument("--project", default="", help="按项目过滤，例如 demo-saas")
    parser.add_argument("--type", default="", help="按页面类型过滤，例如 概念、项目周报、ADR")
    parser.add_argument("--tag", default="", help="按单个标签过滤")
    parser.add_argument("--show-relations", action="store_true", help="对项目相关结果补充关系与运行记忆")
    args = parser.parse_args()

    terms = tokenize(args.query)
    if not terms:
        print("没有可搜索的关键词。")
        return

    project_filter = args.project.strip().lower()
    type_filter = args.type.strip().lower()
    tag_filter = args.tag.strip().lower()

    pages = [load_page(path) for path in iter_markdown_files()]
    index_by_slug = project_index_by_slug(pages)

    results = []
    for page in pages:
        if not page_matches_filters(
            page,
            project_filter=project_filter,
            type_filter=type_filter,
            tag_filter=tag_filter,
        ):
            continue
        score = score_page(page, terms)
        if score > 0:
            results.append((score, page))

    for score, page in sorted(results, key=lambda item: item[0], reverse=True)[: args.limit]:
        print(f"{score:>3}  {obsidian_link(page['path'], str(page['title']))}  {page['summary']}")
        if args.show_relations:
            for line in relation_summary(page, index_by_slug):
                print(line)


if __name__ == "__main__":
    main()

