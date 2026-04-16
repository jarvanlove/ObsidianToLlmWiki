from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from create_page import ensure_project
from wiki_lib import (
    SCRIPT_DIR,
    VAULT_ROOT,
    append_log,
    normalize_tags,
    render_markdown,
    slugify,
    today_iso,
    write_text,
)


def build_analysis_content(
    *,
    title: str,
    project_slug: str,
    domain: str,
    tags: list[str],
    summary: str,
    question: str,
    conclusion: str,
    evidence: str,
    follow_up: str,
    source_links: list[str],
) -> str:
    frontmatter = {
        "title": title,
        "type": "分析",
        "domain": domain,
        "project": project_slug,
        "status": "常青" if not project_slug else "活跃",
        "tags": tags,
        "updated": today_iso(),
        "summary": summary,
    }
    evidence_lines = [line for line in evidence.splitlines()] if evidence.strip() else ["- "]
    follow_up_lines = [line for line in follow_up.splitlines()] if follow_up.strip() else ["- "]
    source_section = source_links if source_links else ["- "]
    body_lines = [
        f"# {title}",
        "",
        "## 问题",
        "",
        question.strip() or "- ",
        "",
        "## 结论",
        "",
        conclusion.strip() or "- ",
        "",
        "## 证据",
        "",
        *evidence_lines,
        "",
        "## 关联来源",
        "",
        *source_section,
        "",
        "## 后续动作",
        "",
        *follow_up_lines,
    ]
    return render_markdown(frontmatter, "\n".join(body_lines))


def main() -> None:
    parser = argparse.ArgumentParser(description="把一次查询或问答沉淀为分析页。")
    parser.add_argument("--title", required=True, help="分析页标题")
    parser.add_argument("--question", required=True, help="原始问题")
    parser.add_argument("--conclusion", required=True, help="结论")
    parser.add_argument("--project", default="", help="所属项目名")
    parser.add_argument("--tags", default="", help="英文逗号分隔标签")
    parser.add_argument("--summary", default="", help="一句话摘要")
    parser.add_argument("--evidence", default="", help="证据内容，可多行")
    parser.add_argument("--follow-up", default="", help="后续动作，可多行")
    parser.add_argument("--source-link", action="append", default=[], help="相关 wiki 链接或路径，可重复传入")
    args = parser.parse_args()

    title = args.title.strip()
    project_name = args.project.strip()
    project_slug = slugify(project_name) if project_name else ""
    tags = normalize_tags(args.tags)
    summary = args.summary.strip() or f"{title} 的查询沉淀。"

    if project_name:
        root = ensure_project(project_name, tags=[], status="活跃", summary=f"{project_name} 的项目知识库。")
        destination = root / "notes" / f"{slugify(title)}.md"
        domain = "项目"
    else:
        destination = VAULT_ROOT / "40_outputs" / "analyses" / f"{slugify(title)}.md"
        domain = "输出"

    content = build_analysis_content(
        title=title,
        project_slug=project_slug,
        domain=domain,
        tags=tags,
        summary=summary,
        question=args.question,
        conclusion=args.conclusion,
        evidence=args.evidence,
        follow_up=args.follow_up,
        source_links=args.source_link,
    )
    write_text(destination, content)

    append_log(
        "查询",
        title,
        f"已沉淀查询结果到 {destination.relative_to(VAULT_ROOT).as_posix()}",
    )
    subprocess.run([sys.executable, str(SCRIPT_DIR / "sync_source_notes.py")], check=True)
    subprocess.run([sys.executable, str(SCRIPT_DIR / "rebuild_indexes.py")], check=True)
    print(destination)


if __name__ == "__main__":
    main()
