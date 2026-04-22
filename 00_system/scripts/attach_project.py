from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from wiki_lib import (
    SCRIPT_DIR,
    detect_wiki_root,
    normalize_tags,
    persist_user_wiki_root,
    slugify,
    write_text,
)


def project_file_map(project_slug: str) -> dict[str, str]:
    base = f"20_projects/active/{project_slug}"
    return {
        "project_index": f"{base}/索引.md",
        "project_overview": f"{base}/概览.md",
        "project_architecture": f"{base}/架构.md",
        "project_decisions": f"{base}/决策.md",
        "project_tasks": f"{base}/任务.md",
        "project_sources": f"{base}/来源.md",
        "project_relations": f"{base}/关系.md",
        "project_risks": f"{base}/风险.md",
        "project_timeline": f"{base}/时间线.md",
        "project_memory": f"{base}/project.memory.md",
    }


def render_bootstrap(title: str, repo_root: Path, wiki_root: Path, project_slug: str) -> str:
    file_map = project_file_map(project_slug)
    lines = [
        f"# {title}",
        "",
        "This workspace is attached to an ObsidianToWiki project memory.",
        "",
        "Read `wiki.context.json` first if it exists. Use the paths below as the human-readable bridge into the wiki.",
        "",
        f"- wiki_root: `{wiki_root}`",
        f"- project_repo_root: `{repo_root}`",
        f"- project_slug: `{project_slug}`",
    ]
    for key, value in file_map.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Working Rules",
            "",
            "- Treat the wiki as the durable project memory layer.",
            "- Read the project index and core pages before making durable changes.",
            "- Write reusable conclusions back into the wiki.",
            "- Reuse shared patterns when similar problems have already been solved elsewhere.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_context(repo_root: Path, wiki_root: Path, project_slug: str) -> str:
    payload = {
        "wiki_root": str(wiki_root),
        "project_repo_root": str(repo_root),
        "project_slug": project_slug,
        **project_file_map(project_slug),
        "shared_index": "30_shared/索引.md",
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def projects_registry_path(wiki_root: Path) -> Path:
    return wiki_root / "00_system" / "registry" / "projects.json"


def load_registry(wiki_root: Path) -> list[dict[str, object]]:
    registry_path = projects_registry_path(wiki_root)
    if not registry_path.exists():
        return []
    try:
        payload = json.loads(registry_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if isinstance(payload, list):
        return payload
    return []


def save_registry(wiki_root: Path, items: list[dict[str, object]]) -> None:
    registry_path = projects_registry_path(wiki_root)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    write_text(registry_path, json.dumps(items, ensure_ascii=False, indent=2))


def upsert_registry_entry(*, project_slug: str, project_name: str, repo_root: Path, wiki_root: Path) -> None:
    items = load_registry(wiki_root)
    entry = {
        "project_slug": project_slug,
        "project_name": project_name,
        "project_repo_root": str(repo_root),
        "wiki_root": str(wiki_root),
        "project_index": project_file_map(project_slug)["project_index"],
    }
    replaced = False
    for index, existing in enumerate(items):
        if str(existing.get("project_slug") or "") == project_slug:
            items[index] = entry
            replaced = True
            break
    if not replaced:
        items.append(entry)
    items.sort(key=lambda item: str(item.get("project_slug") or ""))
    save_registry(wiki_root, items)


def append_log_entry(wiki_root: Path, kind: str, title: str, details: str) -> None:
    log_path = wiki_root / "log.md"
    if not log_path.exists():
        write_text(log_path, "# 日志\n")
    timestamp = datetime.now().replace(microsecond=0).isoformat()
    entry = f"## [{timestamp}] {kind} | {title}\n\n- actor: agent\n- details: {details}\n\n"
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(entry)


def main() -> None:
    parser = argparse.ArgumentParser(description="把一个项目仓库接入 ObsidianToWiki 中心 wiki。")
    parser.add_argument("--repo-root", required=True, help="项目仓库根目录")
    parser.add_argument("--project", required=True, help="项目名")
    parser.add_argument("--wiki-root", default="", help="中心 wiki 根目录")
    parser.add_argument("--tags", default="", help="项目标签，英文逗号分隔")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.exists():
        raise SystemExit(f"项目仓库不存在: {repo_root}")
    try:
        wiki_root = detect_wiki_root(repo_root=repo_root, explicit_root=args.wiki_root.strip())
    except FileNotFoundError as exc:
        raise SystemExit(str(exc))

    project_name = args.project.strip()
    project_slug = slugify(project_name)
    tags = normalize_tags(args.tags)

    env = dict(os.environ)
    env["OBSIDIAN_WIKI_ROOT"] = str(wiki_root)
    subprocess.run(
        [
            sys.executable,
            str(SCRIPT_DIR / "create_page.py"),
            "--title",
            project_name,
            "--type",
            "项目",
            "--tags",
            ",".join(tags),
            "--summary",
            f"{project_name} 的项目知识库。",
        ],
        check=True,
        env=env,
    )

    write_text(repo_root / "wiki.context.json", render_context(repo_root, wiki_root, project_slug))
    bootstrap = render_bootstrap("AGENTS.md", repo_root, wiki_root, project_slug)
    write_text(repo_root / "AGENTS.md", bootstrap)
    bootstrap = render_bootstrap("CLAUDE.md", repo_root, wiki_root, project_slug)
    write_text(repo_root / "CLAUDE.md", bootstrap)

    upsert_registry_entry(
        project_slug=project_slug,
        project_name=project_name,
        repo_root=repo_root,
        wiki_root=wiki_root,
    )
    config_path = persist_user_wiki_root(wiki_root)

    append_log_entry(
        wiki_root,
        "项目",
        f"接入 {project_name}",
        f"repo_root: {repo_root} | wiki_root: {wiki_root} | project_slug: {project_slug} | user_config: {config_path}",
    )
    subprocess.run([sys.executable, str(SCRIPT_DIR / "rebuild_indexes.py")], check=True, env=env)
    print(repo_root / "wiki.context.json")


if __name__ == "__main__":
    main()
