from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from create_page import ensure_project
from schema_lib import page_link
from wiki_lib import (
    SCRIPT_DIR,
    VAULT_ROOT,
    append_log,
    load_page,
    normalize_tags,
    render_markdown,
    slugify,
    today_iso,
    update_page_frontmatter,
    write_text,
)


DESTINATION_TYPES = {
    "project": ("分析", "项目"),
    "personal": ("综述", "个人"),
    "shared": ("模式", "共享"),
    "outputs": ("分析", "输出"),
}


def section_text(body: str, heading: str) -> str:
    marker = f"## {heading}"
    if marker not in body:
        return ""
    start = body.index(marker) + len(marker)
    next_pos = body.find("\n## ", start)
    return body[start: next_pos if next_pos != -1 else len(body)].strip()


def list_items(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def wiki_link(rel_path: str, title: str) -> str:
    return page_link(rel_path, title)


def destination_path(destination: str, title: str, project_slug: str) -> Path:
    slug = slugify(title)
    if destination == "project":
        if not project_slug:
            raise SystemExit("提升到项目层需要章节笔记包含 project，或传入 --project。")
        root = ensure_project(project_slug, tags=[], status="活跃", summary=f"{project_slug} 的项目知识库。")
        return root / "notes" / f"{slug}.md"
    if destination == "personal":
        return VAULT_ROOT / "10_personal" / "syntheses" / f"{slug}.md"
    if destination == "shared":
        return VAULT_ROOT / "30_shared" / "patterns" / f"{slug}.md"
    return VAULT_ROOT / "40_outputs" / "analyses" / f"{slug}.md"


def build_formal_page(
    *,
    title: str,
    destination: str,
    project_slug: str,
    tags: list[str],
    summary: str,
    source_link: str,
    source_refs: list[str],
    source_note: str,
    document_map: str,
    theme: str,
    concepts: str,
    facts: str,
    process: str,
    excerpt: str,
    follow_up: str,
) -> str:
    note_type, domain = DESTINATION_TYPES[destination]
    frontmatter = {
        "title": title,
        "type": note_type,
        "domain": domain,
        "project": project_slug if destination == "project" else "",
        "status": "活跃" if destination == "project" else "常青",
        "tags": tags,
        "updated": today_iso(),
        "summary": summary,
        "source_sections": [source_link],
        "source_refs": source_refs,
    }
    body = "\n".join(
        [
            f"# {title}",
            "",
            "## 结论摘要",
            "",
            theme or "- 待补充。",
            "",
            "## 关键概念",
            "",
            concepts or "- 待补充。",
            "",
            "## 关键事实",
            "",
            facts or "- 待补充。",
            "",
            "## 操作步骤或流程",
            "",
            process or "- 待补充。",
            "",
            "## 证据与出处",
            "",
            f"- 来源章节: {source_link}",
            f"- source_refs: {', '.join(f'`{ref}`' for ref in source_refs) if source_refs else '待补充'}",
            f"- 来源笔记: `{source_note or '待补充'}`",
            f"- 文档地图: `{document_map or '待补充'}`",
            "",
            "## 原文摘录",
            "",
            excerpt or "- 待补充。",
            "",
            "## 适用边界",
            "",
            "- 由章节笔记提升生成，使用前应回到来源章节和原文核对。",
            "",
            "## 后续动作",
            "",
            follow_up or "- 待补充。",
        ]
    )
    return render_markdown(frontmatter, body)


def append_source_to_existing(path: Path, *, title: str, source_link: str, source_refs: list[str], facts: str) -> None:
    text = path.read_text(encoding="utf-8")
    if source_link in text:
        return
    addition = "\n\n".join(
        [
            "## 来源章节补充",
            "",
            f"- 来源章节: {source_link}",
            f"- source_refs: {', '.join(f'`{ref}`' for ref in source_refs) if source_refs else '待补充'}",
            "",
            "### 补充事实",
            "",
            facts or "- 待补充。",
        ]
    )
    write_text(path, text.rstrip() + "\n\n" + addition)


def main() -> None:
    parser = argparse.ArgumentParser(description="把单个章节笔记提升为正式知识页。")
    parser.add_argument("--section", required=True, help="章节笔记路径")
    parser.add_argument("--destination", required=True, choices=sorted(DESTINATION_TYPES), help="目标层")
    parser.add_argument("--title", default="", help="正式知识页标题，默认沿用章节标题")
    parser.add_argument("--project", default="", help="覆盖章节笔记中的 project slug")
    parser.add_argument("--tags", default="", help="额外标签，英文逗号分隔")
    parser.add_argument("--rebuild", action="store_true", help="提升后重建索引")
    args = parser.parse_args()

    section_path = Path(args.section).expanduser().resolve()
    if not section_path.exists():
        raise SystemExit(f"章节笔记不存在: {section_path}")

    page = load_page(section_path)
    frontmatter = page["frontmatter"]
    if not isinstance(frontmatter, dict):
        raise SystemExit("章节笔记缺少 frontmatter。")
    if str(frontmatter.get("type") or "").strip() != "章节笔记":
        raise SystemExit("只支持提升 `章节笔记` 类型页面。")

    rel_path = str(page["rel_path"])
    source_link = wiki_link(rel_path, str(page["title"]))
    source_refs = list_items(frontmatter.get("source_refs"))
    project_slug = args.project.strip() or str(frontmatter.get("project") or "").strip()
    body = str(page["body"])
    title = args.title.strip() or str(frontmatter.get("title") or section_path.stem)
    tags = sorted(set([str(tag) for tag in page["tags"]] + normalize_tags(args.tags)))
    theme = section_text(body, "本节主题")
    concepts = section_text(body, "关键概念")
    facts = section_text(body, "关键事实")
    process = section_text(body, "操作步骤或流程")
    excerpt = section_text(body, "原文摘录")
    follow_up = section_text(body, "待追问问题")
    source_note = str(frontmatter.get("source_note") or "").strip()
    document_map = str(frontmatter.get("document_map") or "").strip()
    summary = str(frontmatter.get("summary") or f"{title} 的来源提升页。")

    target_path = destination_path(args.destination, title, project_slug)
    if target_path.exists():
        append_source_to_existing(target_path, title=title, source_link=source_link, source_refs=source_refs, facts=facts)
    else:
        content = build_formal_page(
            title=title,
            destination=args.destination,
            project_slug=project_slug,
            tags=tags,
            summary=summary,
            source_link=source_link,
            source_refs=source_refs,
            source_note=source_note,
            document_map=document_map,
            theme=theme,
            concepts=concepts,
            facts=facts,
            process=process,
            excerpt=excerpt,
            follow_up=follow_up,
        )
        write_text(target_path, content)

    update_page_frontmatter(
        section_path,
        {
            "status": "已提升",
            "promoted_to": target_path.relative_to(VAULT_ROOT).as_posix(),
            "updated": today_iso(),
        },
    )
    append_log(
        "更新",
        title,
        f"已将章节笔记 {rel_path} 提升到 {target_path.relative_to(VAULT_ROOT).as_posix()}",
    )
    subprocess.run([sys.executable, str(SCRIPT_DIR / "sync_source_notes.py")], check=True)
    if args.rebuild:
        subprocess.run([sys.executable, str(SCRIPT_DIR / "rebuild_indexes.py")], check=True)
    print(target_path)


if __name__ == "__main__":
    main()
