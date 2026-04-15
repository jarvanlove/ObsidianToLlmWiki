from __future__ import annotations

from pathlib import Path

from wiki_lib import (
    VAULT_ROOT,
    grouped,
    iter_markdown_files,
    load_page,
    obsidian_link,
    parse_date,
    today_iso,
    write_text,
)


def list_lines(items: list[dict[str, object]]) -> list[str]:
    lines: list[str] = []
    for item in sorted(items, key=lambda entry: str(entry["title"]).lower()):
        summary = str(item["summary"] or "").strip()
        suffix = f" - {summary}" if summary else ""
        lines.append(f"- {obsidian_link(item['path'], str(item['title']))}{suffix}")
    return lines or ["- 暂无。"]


def section_items(prefix: str) -> list[dict[str, object]]:
    pages = []
    for path in iter_markdown_files():
        rel = path.relative_to(VAULT_ROOT).as_posix()
        if rel.startswith(prefix):
            pages.append(load_page(path))
    return pages


def build_root_index(all_pages: list[dict[str, object]]) -> str:
    project_pages = [
        page
        for page in all_pages
        if page["rel_path"].startswith("20_projects/active/") and page["rel_path"].endswith("/索引.md")
    ]
    dated_pages = []
    for page in all_pages:
        frontmatter = page["frontmatter"]
        if not isinstance(frontmatter, dict):
            continue
        updated = parse_date(str(frontmatter.get("updated") or ""))
        if updated is not None:
            dated_pages.append((updated, page))
    recently_updated = [
        page
        for _, _, page in sorted(
            ((updated, str(page["rel_path"]), page) for updated, page in dated_pages),
            key=lambda item: (item[0], item[1]),
            reverse=True,
        )[:10]
    ]

    lines = [
        "# 总索引",
        "",
        f"最近重建: {today_iso()}",
        "",
        "## 分区入口",
        "",
        "- [[Home]]",
        "- [[10_personal/索引|个人知识]]",
        "- [[20_projects/索引|项目知识]]",
        "- [[30_shared/索引|共享知识]]",
        "- [[40_outputs/索引|输出沉淀]]",
        "- [[log|操作日志]]",
        "",
        "## 进行中的项目",
        "",
    ]
    lines.extend(list_lines(project_pages))
    lines.extend(["", "## 最近更新", ""])
    lines.extend(list_lines(recently_updated))
    return "\n".join(lines)


def build_section_index(title: str, pages: list[dict[str, object]], type_groups: list[tuple[str, str]]) -> str:
    lines = [f"# {title}", "", f"最近重建: {today_iso()}", ""]
    grouped_pages = grouped(pages, "type")
    for heading, page_type in type_groups:
        lines.extend([f"## {heading}", ""])
        filtered = [
            page
            for page in grouped_pages.get(page_type, [])
            if not str(page["rel_path"]).endswith("/索引.md") and not str(page["rel_path"]).endswith("索引.md")
        ]
        lines.extend(list_lines(filtered))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_projects_index(pages: list[dict[str, object]]) -> str:
    active_projects = [
        page
        for page in pages
        if page["rel_path"].startswith("20_projects/active/") and page["rel_path"].endswith("/索引.md")
    ]
    archived_projects = [
        page
        for page in pages
        if page["rel_path"].startswith("20_projects/archive/") and page["rel_path"].endswith("/索引.md")
    ]
    lines = ["# 项目索引", "", f"最近重建: {today_iso()}", "", "## 进行中", ""]
    lines.extend(list_lines(active_projects))
    lines.extend(["", "## 已归档", ""])
    lines.extend(list_lines(archived_projects))
    return "\n".join(lines)


def build_project_local_index(project_index_path: Path) -> str:
    project_root = project_index_path.parent
    project_name = project_root.name
    overview = project_root / "概览.md"
    architecture = project_root / "架构.md"
    decisions = project_root / "决策.md"
    learnings = project_root / "经验.md"
    tasks = project_root / "任务.md"
    sources = project_root / "来源.md"
    notes = sorted(project_root.joinpath("notes").glob("*.md"))
    source_notes = sorted(project_root.joinpath("source-notes").glob("*.md"))

    lines = [
        "# " + project_name.replace("-", " "),
        "",
        f"最近重建: {today_iso()}",
        "",
        "## 核心页面",
        "",
        f"- {obsidian_link(overview, '概览')}",
        f"- {obsidian_link(architecture, '架构')}",
        f"- {obsidian_link(decisions, '决策')}",
        f"- {obsidian_link(learnings, '经验')}",
        f"- {obsidian_link(tasks, '任务')}",
        f"- {obsidian_link(sources, '来源')}",
        "",
        "## 笔记",
        "",
    ]
    lines.extend(list_lines([load_page(path) for path in notes]))
    lines.extend(["", "## 来源笔记", ""])
    lines.extend(list_lines([load_page(path) for path in source_notes]))
    return "\n".join(lines)


def main() -> None:
    all_pages = [load_page(path) for path in iter_markdown_files()]

    personal_pages = section_items("10_personal/")
    shared_pages = section_items("30_shared/")
    output_pages = section_items("40_outputs/")
    project_pages = section_items("20_projects/")

    write_text(VAULT_ROOT / "index.md", build_root_index(all_pages))
    write_text(
        VAULT_ROOT / "10_personal" / "索引.md",
        build_section_index(
            "个人索引",
            personal_pages,
            [("领域", "领域"), ("概念", "概念"), ("实体", "实体"), ("综述", "综述")],
        ),
    )
    write_text(VAULT_ROOT / "20_projects" / "索引.md", build_projects_index(project_pages))
    write_text(
        VAULT_ROOT / "30_shared" / "索引.md",
        build_section_index(
            "共享索引",
            shared_pages,
            [("模式", "模式"), ("工具", "工具"), ("架构", "架构"), ("提示词", "提示词")],
        ),
    )
    write_text(
        VAULT_ROOT / "40_outputs" / "索引.md",
        build_section_index("输出索引", output_pages, [("分析", "分析"), ("简报", "简报")]),
    )

    for path in (VAULT_ROOT / "20_projects" / "active").glob("*/索引.md"):
        write_text(path, build_project_local_index(path))
    for path in (VAULT_ROOT / "20_projects" / "archive").glob("*/索引.md"):
        write_text(path, build_project_local_index(path))

    print("Indexes rebuilt.")


if __name__ == "__main__":
    main()
