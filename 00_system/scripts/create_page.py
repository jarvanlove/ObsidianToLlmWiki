from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from wiki_lib import (
    SCRIPT_DIR,
    VAULT_ROOT,
    append_log,
    format_tags,
    normalize_tags,
    render_template,
    slugify,
    today_iso,
    write_text,
)

TEMPLATE_DIR = VAULT_ROOT / "00_system" / "templates"

TYPE_ALIASES = {
    "area": "领域",
    "concept": "概念",
    "entity": "实体",
    "synthesis": "综述",
    "pattern": "模式",
    "tool": "工具",
    "architecture": "架构",
    "prompt": "提示词",
    "analysis": "分析",
    "briefing": "简报",
    "source": "来源",
    "project": "项目",
    "adr": "ADR",
    "weekly": "项目周报",
    "weekly-report": "项目周报",
    "retro": "项目复盘",
    "retrospective": "项目复盘",
}

GLOBAL_TYPE_MAP = {
    "领域": ("10_personal/areas", "generic-note.md", "个人"),
    "概念": ("10_personal/concepts", "concept.md", "个人"),
    "实体": ("10_personal/entities", "entity.md", "个人"),
    "综述": ("10_personal/syntheses", "generic-note.md", "个人"),
    "模式": ("30_shared/patterns", "pattern.md", "共享"),
    "工具": ("30_shared/tools", "generic-note.md", "共享"),
    "架构": ("30_shared/architectures", "generic-note.md", "共享"),
    "提示词": ("30_shared/prompts", "generic-note.md", "共享"),
    "分析": ("40_outputs/analyses", "analysis.md", "输出"),
    "简报": ("40_outputs/briefings", "analysis.md", "输出"),
    "来源": ("01_inbox/clips", "source-note.md", "个人"),
}


def run_rebuild() -> None:
    subprocess.run([sys.executable, str(SCRIPT_DIR / "rebuild_indexes.py")], check=True)


def project_root(project_slug: str) -> Path:
    return VAULT_ROOT / "20_projects" / "active" / project_slug


def normalize_type(raw_type: str) -> str:
    normalized = raw_type.strip()
    return TYPE_ALIASES.get(normalized.lower(), normalized)


def template_variables(
    *,
    title: str,
    note_type: str,
    domain: str,
    project: str,
    tags: list[str],
    status: str,
    summary: str,
) -> dict[str, str]:
    return {
        "title": title,
        "type": note_type,
        "domain": domain,
        "project": project,
        "project_slug": project,
        "tags": format_tags(tags),
        "status": status,
        "updated": today_iso(),
        "summary": summary,
    }


def ensure_project(project_name: str, tags: list[str], status: str, summary: str) -> Path:
    slug = slugify(project_name)
    root = project_root(slug)
    (root / "notes").mkdir(parents=True, exist_ok=True)
    (root / "source-notes").mkdir(parents=True, exist_ok=True)
    (root / "sources").mkdir(parents=True, exist_ok=True)

    files = {
        "索引.md": "project-index.md",
        "概览.md": "project-overview.md",
        "架构.md": "project-architecture.md",
        "决策.md": "project-decisions.md",
        "经验.md": "project-learnings.md",
        "来源.md": "project-sources.md",
        "任务.md": "project-tasks.md",
    }

    for file_name, template_name in files.items():
        path = root / file_name
        if path.exists():
            continue
        variables = template_variables(
            title=project_name,
            note_type="项目" if file_name == "索引.md" else file_name.replace(".md", ""),
            domain="项目",
            project=slug,
            tags=tags,
            status=status,
            summary=summary or f"{project_name} 的项目知识库。",
        )
        content = render_template(TEMPLATE_DIR / template_name, variables)
        write_text(path, content)

    append_log("项目", project_name, f"已创建项目知识库 20_projects/active/{slug}")
    return root


def create_global_page(args: argparse.Namespace) -> Path:
    folder_name, template_name, domain = GLOBAL_TYPE_MAP[args.type]
    slug = slugify(args.title)
    destination = VAULT_ROOT / folder_name / f"{slug}.md"
    if destination.exists():
        return destination

    variables = template_variables(
        title=args.title,
        note_type=args.type,
        domain=domain,
        project=args.project or "",
        tags=normalize_tags(args.tags),
        status=args.status,
        summary=args.summary or f"{args.title} 笔记。",
    )
    content = render_template(TEMPLATE_DIR / template_name, variables)
    write_text(destination, content)
    return destination


def create_project_page(args: argparse.Namespace) -> Path:
    root = ensure_project(
        project_name=args.project or args.title,
        tags=normalize_tags(args.tags),
        status=args.status,
        summary=args.summary or f"{args.project or args.title} 的项目知识库。",
    )

    if args.type == "项目":
        return root / "索引.md"

    slug = slugify(args.title)
    if args.type == "来源":
        destination = root / "source-notes" / f"{slug}.md"
        template_name = "source-note.md"
    else:
        destination = root / "notes" / f"{slug}.md"
        if args.type in {"分析", "简报"}:
            template_name = "analysis.md"
        elif args.type == "ADR":
            template_name = "adr.md"
        elif args.type == "项目周报":
            template_name = "project-weekly-report.md"
        elif args.type == "项目复盘":
            template_name = "project-retrospective.md"
        else:
            template_name = "generic-note.md"

    if destination.exists():
        return destination

    variables = template_variables(
        title=args.title,
        note_type=args.type,
        domain="项目",
        project=slugify(args.project or args.title),
        tags=normalize_tags(args.tags),
        status=args.status,
        summary=args.summary or f"{args.title} 笔记。",
    )
    content = render_template(TEMPLATE_DIR / template_name, variables)
    write_text(destination, content)
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description="在知识库中创建页面或项目脚手架。")
    parser.add_argument("--title", required=True, help="页面标题或项目名")
    parser.add_argument("--type", required=True, help="页面类型，可用中文或英文别名")
    parser.add_argument("--project", default="", help="所属项目名；填写后页面会创建在项目目录中")
    parser.add_argument("--tags", default="", help="英文逗号分隔的标签")
    parser.add_argument("--status", default="活跃", help="页面状态")
    parser.add_argument("--summary", default="", help="一句话摘要")
    args = parser.parse_args()
    args.type = normalize_type(args.type)

    valid_types = sorted(set(GLOBAL_TYPE_MAP) | {"项目", "ADR", "项目周报", "项目复盘"})
    if args.type not in valid_types:
        raise SystemExit(f"不支持的类型: {args.type}。可用类型: {', '.join(valid_types)}")

    if args.type == "项目" or args.project:
        created_path = create_project_page(args)
    else:
        created_path = create_global_page(args)

    append_log(args.type, args.title, f"已创建或确认 {created_path.relative_to(VAULT_ROOT).as_posix()}")
    run_rebuild()
    print(created_path)


if __name__ == "__main__":
    main()
