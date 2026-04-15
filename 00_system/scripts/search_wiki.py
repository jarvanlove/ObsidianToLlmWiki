from __future__ import annotations

import argparse
import re

from wiki_lib import iter_markdown_files, load_page, obsidian_link


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
    if rel_path in {"agents.md", "claude.md", "readme.md", "home.md", "log.md", "index.md"}:
        score -= 12
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


def main() -> None:
    parser = argparse.ArgumentParser(description="对知识库 Markdown 页面执行简单词法检索。")
    parser.add_argument("query", help="搜索词")
    parser.add_argument("--limit", type=int, default=10, help="返回结果数量")
    parser.add_argument("--project", default="", help="按项目过滤，例如 demo-saas")
    parser.add_argument("--type", default="", help="按页面类型过滤，例如 概念、项目周报、ADR")
    parser.add_argument("--tag", default="", help="按单个标签过滤")
    args = parser.parse_args()

    terms = tokenize(args.query)
    if not terms:
        print("没有可搜索的关键词。")
        return

    project_filter = args.project.strip().lower()
    type_filter = args.type.strip().lower()
    tag_filter = args.tag.strip().lower()

    results = []
    for path in iter_markdown_files():
        page = load_page(path)
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


if __name__ == "__main__":
    main()

