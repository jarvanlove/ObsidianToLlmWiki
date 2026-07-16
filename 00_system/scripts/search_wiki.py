from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

from retrieval_index import (
    INDEX_SCHEMA_VERSION,
    best_chunk,
    connect_index,
    index_path_label,
    indexed_pages,
    refresh_index,
    resolve_index_path,
)
from wiki_lib import VAULT_ROOT, append_log, obsidian_link, parse_date


RETRIEVAL_ALIASES_PATH = VAULT_ROOT / "00_system" / "registry" / "retrieval_aliases.json"


def tokenize(text: str) -> list[str]:
    lowered = text.lower()
    tokens: list[str] = []
    for segment in re.findall(r"[\u4e00-\u9fff]+|[a-z0-9]+", lowered):
        candidates = [segment]
        if re.fullmatch(r"[\u4e00-\u9fff]+", segment) and len(segment) > 2:
            candidates.extend(segment[index : index + 2] for index in range(len(segment) - 1))
        for candidate in candidates:
            if candidate not in tokens:
                tokens.append(candidate)
    return tokens


def expand_query_terms(query: str) -> tuple[list[str], dict[str, object]]:
    original_terms = tokenize(query)
    terms = list(original_terms)
    matched_groups: list[str] = []
    try:
        payload = json.loads(RETRIEVAL_ALIASES_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        payload = {}
    groups = payload.get("groups") if isinstance(payload, dict) else []
    lowered_query = query.lower()
    if isinstance(groups, list):
        for group in groups:
            if not isinstance(group, dict):
                continue
            group_id = str(group.get("id") or "").strip()
            aliases = [str(item).strip().lower() for item in group.get("aliases", []) if str(item).strip()] if isinstance(group.get("aliases"), list) else []
            if not group_id or not aliases or not any(alias in lowered_query for alias in aliases):
                continue
            matched_groups.append(group_id)
            for alias in aliases:
                alias_terms = [alias] if re.fullmatch(r"[\u4e00-\u9fff ]+", alias) else tokenize(alias)
                for term in alias_terms:
                    if term not in terms:
                        terms.append(term)
    return terms, {"original_terms": original_terms, "matched_groups": matched_groups}


def page_type_weight(page: dict[str, object]) -> int:
    frontmatter = page["frontmatter"]
    if not isinstance(frontmatter, dict):
        return 0
    page_type = str(frontmatter.get("type") or "").strip()
    rel_path = str(page["rel_path"])

    if page_type in {"项目概览", "项目架构", "项目决策", "项目任务", "项目运行记忆"}:
        return 5
    if page_type in {"概念", "实体", "综述", "模式", "工具", "架构", "提示词"}:
        return 3
    if page_type == "来源":
        return -4
    if page_type in {"分析", "简报"} and rel_path.startswith("40_outputs/"):
        return -3
    if page_type == "反思":
        return -5
    return 0


def extract_body_links(body: str) -> list[str]:
    links = re.findall(r"\[\[([^\]\|#]+)(?:#[^\]\|]+)?(?:\|[^\]]+)?\]\]", body)
    normalized: list[str] = []
    for link in links:
        candidate = str(link).strip()
        if candidate and candidate not in normalized:
            normalized.append(candidate)
    return normalized


def score_page(page: dict[str, object], query_terms: list[str]) -> int:
    title = str(page["title"]).lower()
    rel_path = str(page["rel_path"]).lower()
    summary = str(page["summary"]).lower()
    body = str(page["body"]).lower()
    tags = " ".join(str(tag).lower() for tag in page["tags"])

    if rel_path.startswith("40_outputs/analyses/知识库体检-"):
        return -999

    score = 0
    matched = False
    matched_terms = 0
    for term in query_terms:
        term_matched = False
        if term in title:
            score += 20
            matched = True
            term_matched = True
        if term in rel_path:
            score += 12
            matched = True
            term_matched = True
        if term in tags:
            score += 8
            matched = True
            term_matched = True
        if term in summary:
            score += 6
            matched = True
            term_matched = True
        body_hits = body.count(term)
        if body_hits:
            matched = True
            term_matched = True
        score += body_hits
        if term_matched:
            matched_terms += 1
    if not matched:
        return 0
    score += matched_terms * 6
    if len(query_terms) > 1 and matched_terms == len(query_terms):
        score += 12
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
    score += page_type_weight(page)

    frontmatter = page["frontmatter"]
    if isinstance(frontmatter, dict):
        status = str(frontmatter.get("status") or "").strip()
        if status in {"活跃", "常用", "常青"}:
            score += 4
        if status in {"候选", "已归档"}:
            score -= 4
        if status in {"过期", "废弃"}:
            score -= 6

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
    domain = str(frontmatter.get("domain") or "").strip()
    project_slug = str(frontmatter.get("project") or "").strip()
    body_links = extract_body_links(str(page["body"]))
    if domain == "个人":
        lines: list[str] = []
        related_to = frontmatter.get("related_to") if isinstance(frontmatter.get("related_to"), list) else []
        builds_on = frontmatter.get("builds_on") if isinstance(frontmatter.get("builds_on"), list) else []
        if related_to:
            lines.append(f"    related_to: {', '.join(str(item) for item in related_to)}")
        if builds_on:
            lines.append(f"    builds_on: {', '.join(str(item) for item in builds_on)}")
        if project_slug:
            lines.append(f"    source_project: {project_slug}")
        if body_links:
            lines.append(f"    linked_pages: {', '.join(body_links[:4])}")
        return lines
    if domain == "共享":
        lines = []
        if project_slug:
            lines.append(f"    source_project: {project_slug}")
        if body_links:
            lines.append(f"    linked_pages: {', '.join(body_links[:4])}")
        tags = frontmatter.get("tags") if isinstance(frontmatter.get("tags"), list) else []
        if tags:
            lines.append(f"    tags: {', '.join(str(tag) for tag in tags[:5])}")
        return lines
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


def list_items(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def build_snippet(text: str, query_terms: list[str], *, max_chars: int = 360) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    if len(normalized) <= max_chars:
        return normalized

    lowered = normalized.lower()
    positions = [lowered.find(term) for term in query_terms if lowered.find(term) >= 0]
    match_at = min(positions) if positions else 0
    start = max(0, match_at - max_chars // 4)
    end = min(len(normalized), start + max_chars)
    if end - start < max_chars:
        start = max(0, end - max_chars)
    prefix = "..." if start else ""
    suffix = "..." if end < len(normalized) else ""
    return f"{prefix}{normalized[start:end].strip()}{suffix}"


def result_payload(
    *,
    rank: int,
    score: int,
    page: dict[str, object],
    chunk: dict[str, object],
    query_terms: list[str],
    relations: list[str],
) -> dict[str, object]:
    frontmatter = page["frontmatter"] if isinstance(page["frontmatter"], dict) else {}
    source_notes = list_items(frontmatter.get("source_notes"))
    source_note = str(frontmatter.get("source_note") or "").strip()
    if source_note and source_note not in source_notes:
        source_notes.append(source_note)
    return {
        "rank": rank,
        "score": score,
        "path": str(page["rel_path"]),
        "title": str(page["title"]),
        "summary": str(page["summary"]),
        "page_type": str(frontmatter.get("type") or ""),
        "domain": str(frontmatter.get("domain") or ""),
        "project": str(frontmatter.get("project") or ""),
        "status": str(frontmatter.get("status") or ""),
        "updated": str(frontmatter.get("updated") or ""),
        "tags": list_items(page.get("tags")),
        "source_notes": source_notes,
        "source_refs": list_items(frontmatter.get("source_refs")),
        "heading": str(chunk.get("heading") or ""),
        "snippet": build_snippet(str(chunk.get("body") or page["body"]), query_terms),
        "relations": [line.strip() for line in relations],
    }


def estimate_tokens(text: str) -> int:
    cjk_count = len(re.findall(r"[\u4e00-\u9fff]", text))
    other_count = len(text) - cjk_count
    return cjk_count + (other_count + 3) // 4


def truncate_to_token_budget(text: str, token_budget: int) -> str:
    if token_budget <= 0:
        return ""
    if estimate_tokens(text) <= token_budget:
        return text
    output: list[str] = []
    for char in text:
        candidate = "".join(output) + char
        if estimate_tokens(candidate) > max(1, token_budget - 2):
            break
        output.append(char)
    return "".join(output).rstrip() + "..."


def render_context_pack(payload: dict[str, object], token_budget: int) -> str:
    filters = payload["filters"] if isinstance(payload.get("filters"), dict) else {}
    filter_text = ", ".join(f"{key}={value}" for key, value in filters.items() if value) or "none"
    lines = [
        "# OTW Context Pack",
        "",
        f"- query: {payload['query']}",
        f"- filters: {filter_text}",
        f"- result_count: {payload['count']}",
        f"- token_budget: {token_budget}",
        "",
    ]
    rendered = "\n".join(lines)

    results = payload["results"] if isinstance(payload.get("results"), list) else []
    for result in results:
        if not isinstance(result, dict):
            continue
        source_notes = result.get("source_notes") if isinstance(result.get("source_notes"), list) else []
        source_refs = result.get("source_refs") if isinstance(result.get("source_refs"), list) else []
        metadata_lines = [
            f"## {result['rank']}. {result['title']}",
            "",
            f"- path: `{result['path']}`",
            f"- type: `{result['page_type']}`",
            f"- project: `{result['project'] or '-'}`",
            f"- updated: `{result['updated'] or '-'}`",
            f"- score: {result['score']}",
            f"- source_notes: {', '.join(str(item) for item in source_notes) if source_notes else '-'}",
            f"- source_refs: {', '.join(str(item) for item in source_refs) if source_refs else '-'}",
            f"- heading: {result['heading'] or '-'}",
            "",
        ]
        block_prefix = "\n".join(metadata_lines)
        remaining = token_budget - estimate_tokens(rendered + "\n" + block_prefix)
        if remaining <= 8:
            break
        snippet = truncate_to_token_budget(str(result.get("snippet") or ""), remaining)
        rendered += f"\n{block_prefix}> {snippet}\n"
        if estimate_tokens(rendered) >= token_budget:
            break

    return rendered.rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="对知识库 Markdown 页面执行本地可追溯检索。")
    parser.add_argument("query", help="搜索词")
    parser.add_argument("--limit", type=int, default=10, help="返回结果数量")
    parser.add_argument("--project", default="", help="按项目过滤，例如 demo-saas")
    parser.add_argument("--type", default="", help="按页面类型过滤，例如 概念、项目周报、ADR")
    parser.add_argument("--tag", default="", help="按单个标签过滤")
    parser.add_argument("--show-relations", action="store_true", help="对项目相关结果补充关系与运行记忆")
    parser.add_argument("--no-log-failures", action="store_true", help="不记录零结果查询")
    parser.add_argument("--format", choices=["text", "json", "context"], default="text", help="输出格式")
    parser.add_argument("--token-budget", type=int, default=4000, help="context 输出的近似 token 上限")
    parser.add_argument("--index-path", default="", help="可选的 SQLite 索引路径")
    parser.add_argument("--no-refresh", action="store_true", help="查询前不检查 Markdown 新鲜度")
    args = parser.parse_args()

    terms, query_expansion = expand_query_terms(args.query)
    if not terms:
        if args.format == "json":
            print(json.dumps({"schema_version": INDEX_SCHEMA_VERSION, "query": args.query, "count": 0, "results": []}, ensure_ascii=False, indent=2))
        else:
            print("没有可搜索的关键词。")
        return

    project_filter = args.project.strip().lower()
    type_filter = args.type.strip().lower()
    tag_filter = args.tag.strip().lower()

    index_path = resolve_index_path(args.index_path or None)
    with connect_index(index_path) as connection:
        if args.no_refresh:
            refresh_stats = {
                "added": 0,
                "updated": 0,
                "deleted": 0,
                "unchanged": 0,
                "indexed_pages": int(connection.execute("SELECT COUNT(*) FROM pages").fetchone()[0]),
            }
        else:
            refresh_stats = refresh_index(connection).to_dict()
        pages = indexed_pages(connection)
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

        sorted_results = sorted(results, key=lambda item: (-item[0], str(item[1]["rel_path"])))
        selected_results = sorted_results[: max(args.limit, 0)]
        structured_results = []
        for rank, (score, page) in enumerate(selected_results, start=1):
            relations = relation_summary(page, index_by_slug) if args.show_relations else []
            structured_results.append(
                result_payload(
                    rank=rank,
                    score=score,
                    page=page,
                    chunk=best_chunk(connection, str(page["rel_path"]), terms),
                    query_terms=terms,
                    relations=relations,
                )
            )

    payload = {
        "schema_version": INDEX_SCHEMA_VERSION,
        "query": args.query,
        "terms": terms,
        "query_expansion": query_expansion,
        "filters": {"project": project_filter, "type": type_filter, "tag": tag_filter},
        "retrieval": {
            "backend": "sqlite-fts5",
            "index_path": index_path_label(index_path),
            "refresh": refresh_stats,
        },
        "count": len(structured_results),
        "total_matches": len(sorted_results),
        "results": structured_results,
    }

    if not structured_results:
        if not args.no_log_failures:
            filters = []
            if project_filter:
                filters.append(f"project={project_filter}")
            if type_filter:
                filters.append(f"type={type_filter}")
            if tag_filter:
                filters.append(f"tag={tag_filter}")
            filter_text = ", ".join(filters) if filters else "none"
            append_log("检索", "查询无结果", f"query={args.query}; filters={filter_text}")

    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    if args.format == "context":
        print(render_context_pack(payload, max(args.token_budget, 100)), end="")
        return
    if not structured_results:
        print("没有找到结果。")
        return

    for result in structured_results:
        page_path = Path(str(result["path"]))
        print(f"{int(result['score']):>3}  {obsidian_link(VAULT_ROOT / page_path, str(result['title']))}  {result['summary']}")
        for line in result["relations"]:
            print(f"    {line}")


if __name__ == "__main__":
    main()

