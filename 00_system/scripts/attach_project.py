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

CONTROL_FILE_NAMES = (
    "PRODUCT_SPEC.md",
    "ARCHITECTURE.md",
    "TASKS.md",
    "TESTING.md",
    "SECURITY.md",
    "DEPLOYMENT.md",
    "OPERATIONS.md",
)

MANAGED_BLOCK_START = "<!-- OBSIDIANTOWIKI:PROJECT_CONTROL_START -->"
MANAGED_BLOCK_END = "<!-- OBSIDIANTOWIKI:PROJECT_CONTROL_END -->"


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
    is_codex = title.upper().startswith("AGENTS")
    if is_codex:
        entrypoint = "This file is the Codex entrypoint for this project."
        peer_rule = "Do not treat `CLAUDE.md` as Codex's parent instruction file."
    else:
        entrypoint = "This file is the Claude Code / compatible-tools entrypoint for this project."
        peer_rule = "Do not treat `AGENTS.md` as this tool's parent instruction file."
    lines = [
        f"# {title}",
        "",
        "This workspace is attached to an ObsidianToWiki project memory.",
        entrypoint,
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
            f"- {peer_rule}",
            "- For local implementation tasks, read project control files directly when they exist:",
            "  - `PRODUCT_SPEC.md`",
            "  - `ARCHITECTURE.md`",
            "  - `TASKS.md`",
            "  - `TESTING.md`",
            "  - `SECURITY.md`",
            "  - `DEPLOYMENT.md`",
            "  - `OPERATIONS.md`",
        ]
    )
    return "\n".join(lines) + "\n"


def render_managed_block(title: str, repo_root: Path, wiki_root: Path, project_slug: str) -> str:
    rendered = render_bootstrap(title, repo_root, wiki_root, project_slug).strip()
    return f"{MANAGED_BLOCK_START}\n\n{rendered}\n\n{MANAGED_BLOCK_END}\n"


def upsert_marked_block(path: Path, block: str) -> str:
    if not path.exists():
        write_text(path, block)
        return "created"

    existing = path.read_text(encoding="utf-8")
    start = existing.find(MANAGED_BLOCK_START)
    end = existing.find(MANAGED_BLOCK_END)
    if start != -1 and end != -1 and end > start:
        end += len(MANAGED_BLOCK_END)
        updated = existing[:start].rstrip() + "\n\n" + block.rstrip() + "\n" + existing[end:].lstrip()
        write_text(path, updated)
        return "updated"

    updated = existing.rstrip() + "\n\n" + block.rstrip() + "\n"
    write_text(path, updated)
    return "appended"


def render_context(repo_root: Path, wiki_root: Path, project_slug: str) -> str:
    payload = {
        "wiki_root": str(wiki_root),
        "project_repo_root": str(repo_root),
        "project_slug": project_slug,
        **project_file_map(project_slug),
        "shared_index": "30_shared/索引.md",
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def detect_project_shape(repo_root: Path) -> dict[str, object]:
    package_json = repo_root / "package.json"
    frontend_package_jsons = list(repo_root.glob("*/package.json"))
    pom_xml = repo_root / "pom.xml"
    nested_poms = list(repo_root.glob("*/pom.xml"))
    requirements = sorted({*repo_root.glob("requirements*.txt"), *repo_root.glob("*/requirements*.txt")})
    docker_compose = sorted(path.name for path in repo_root.glob("docker-compose*.yml"))
    has_python_scripts = any(repo_root.glob("00_system/scripts/*.py")) or any(repo_root.glob("*.py"))

    return {
        "has_root_package_json": package_json.exists(),
        "frontend_package_jsons": [str(path.relative_to(repo_root)) for path in frontend_package_jsons],
        "has_root_pom": pom_xml.exists(),
        "nested_poms": [str(path.relative_to(repo_root)) for path in nested_poms],
        "requirements": [str(path.relative_to(repo_root)) for path in requirements[:10]],
        "docker_compose": docker_compose,
        "has_python_scripts": has_python_scripts,
    }


def render_product_spec(project_name: str, project_slug: str) -> str:
    return f"""# Product Spec

## Product

- Name: {project_name}
- Project slug: `{project_slug}`
- Target users: TODO
- Core problem: TODO
- Promise: TODO

## Current Scope

Must have:

- TODO

Explicitly not doing unless added to `TASKS.md`:

- TODO

## Core User Flows

### Flow 1

- Entry: TODO
- Steps: TODO
- Success: TODO
- Failure states: TODO

## Acceptance Criteria

- Every non-trivial task is represented in `TASKS.md`.
- Scope changes update this file before implementation.
- Implementation work follows `ARCHITECTURE.md` and is verified through `TESTING.md`.

## Change Log

| Date | Change | Reason | Impact |
|---|---|---|---|
| {datetime.now().date().isoformat()} | Project control files initialized | Attach project to ObsidianToWiki AI workflow | Documentation/control-plane only |
"""


def render_architecture(project_name: str, shape: dict[str, object]) -> str:
    package_lines: list[str] = []
    if shape["has_root_package_json"]:
        package_lines.append("- Root `package.json` detected.")
    for item in shape["frontend_package_jsons"]:
        package_lines.append(f"- Nested package detected: `{item}`.")
    if shape["has_root_pom"]:
        package_lines.append("- Root `pom.xml` detected.")
    for item in shape["nested_poms"]:
        package_lines.append(f"- Nested Maven module detected: `{item}`.")
    for item in shape["requirements"]:
        package_lines.append(f"- Python requirements detected: `{item}`.")
    if shape["docker_compose"]:
        package_lines.append("- Docker compose files: " + ", ".join(f"`{name}`" for name in shape["docker_compose"]) + ".")
    if not package_lines:
        package_lines.append("- TODO: document project runtime and framework shape.")

    detected = "\n".join(package_lines)
    return f"""# Architecture

## System Shape

{detected}

## Module Boundaries

| Module | Owns | Must not do |
|---|---|---|
| TODO | TODO | TODO |

## Data / Contract Boundaries

- Data model: TODO
- API contract: TODO
- Auth/permission model: TODO
- External integrations: TODO

## Invariants

- Do not change module boundaries without updating this file.
- Do not change public behavior without updating tests or acceptance criteria.
- Do not introduce new infrastructure without an explicit task and rationale.

## Architecture Decisions

Record durable architecture decisions in `docs/adr/` or the project wiki decisions page.
"""


def render_tasks() -> str:
    today = datetime.now().date().isoformat()
    return f"""# Tasks

## Now

| ID | Task | Risk | Acceptance | Status |
|---|---|---|---|---|
| CTRL-001 | Adopt ObsidianToWiki project control files | P3 | Control files exist and entrypoints reference them without overwriting project-specific rules | Done |

## Next

- Fill TODO fields in `PRODUCT_SPEC.md` and `ARCHITECTURE.md`.
- Add a one-command verification path if the project does not have one.

## Blocked

- None.

## Done

- {today}: Initialized project-level AI control files.
"""


def render_testing(shape: dict[str, object]) -> str:
    command_lines: list[str] = []
    if shape["has_root_package_json"]:
        command_lines.extend(
            [
                "```bash",
                "npm install",
                "npm run build",
                "# TODO: add lint/test/typecheck commands if available",
                "```",
            ]
        )
    for item in shape["frontend_package_jsons"]:
        parent = Path(item).parent.as_posix()
        command_lines.extend(
            [
                "```bash",
                f"cd {parent}",
                "npm install",
                "npm run build",
                "# TODO: add lint/test/typecheck commands if available",
                "```",
            ]
        )
    if shape["has_root_pom"]:
        command_lines.extend(["```bash", "mvn test", "mvn -DskipTests package", "```"])
    for item in shape["nested_poms"]:
        parent = Path(item).parent.as_posix()
        command_lines.extend(["```bash", f"cd {parent}", "mvn test", "mvn -DskipTests package", "```"])
    for item in shape["requirements"]:
        parent = Path(item).parent.as_posix()
        command_lines.extend(
            [
                "```bash",
                f"cd {parent}",
                f"pip install -r {Path(item).name}",
                "# TODO: add pytest or service startup command if available",
                "```",
            ]
        )
    if not command_lines:
        command_lines.append("TODO: document install, lint, test, build, and manual verification commands.")

    commands = "\n\n".join(command_lines)
    return f"""# Testing

## Commands

{commands}

## Minimum Verification Matrix

| Change type | Required checks |
|---|---|
| Documentation/config only | Read-through and affected-link check |
| UI/frontend | Build/typecheck/lint where available plus manual UI smoke |
| Backend/domain/API | Targeted test plus startup/request smoke |
| Database/auth/security/deployment | Dedicated review, migration/rollback notes, and manual smoke |

## Completion Rule

Report exact commands run. If commands are TODO or cannot run locally, state the blocker and the remaining risk.
"""


def render_security() -> str:
    return """# Security

## Sensitive Areas

- Authentication and authorization.
- User data and private files.
- Secrets, API keys, tokens, and environment files.
- Database migrations and destructive operations.
- File upload/download and path handling.
- External integrations and callbacks.

## Rules

- Do not commit real secrets.
- Do not weaken authentication, authorization, or validation without explicit task scope.
- Treat database migrations, data deletion, payment, permission, and deployment changes as high risk.
- Add or identify security-relevant tests for auth, permission, file, and integration changes.

## Incident Response

1. Preserve logs and reproduction steps.
2. Rotate affected secrets if needed.
3. Patch with a regression test or documented manual verification.
4. Update this file or `OPERATIONS.md` if a repeatable prevention rule is learned.
"""


def render_deployment(shape: dict[str, object]) -> str:
    compose = shape["docker_compose"]
    compose_lines = "\n".join(f"- `{name}`" for name in compose) if compose else "- TODO: document deployment entrypoints."
    return f"""# Deployment

## Environments

- Local development: TODO
- Staging: TODO
- Production: TODO

## Known Deployment Files

{compose_lines}

## Deploy Steps

TODO: document exact deploy steps for this project.

## Environment Variables

TODO: document required environment variables. Do not commit real secrets.

## Rollback

TODO: document rollback steps. At minimum, identify how to restore the previous application version and configuration.
"""


def render_operations() -> str:
    return """# Operations

## Runtime Checks

- TODO: service URLs / ports.
- TODO: health checks.
- TODO: key logs.

## Common Incidents

| Symptom | Check | Likely fix |
|---|---|---|
| TODO | TODO | TODO |

## Data and Backup

- TODO: database/storage backup path.
- TODO: restore procedure.

## Maintenance Rules

- Prefer targeted restarts over full restarts.
- Do not run destructive commands without verified target paths and explicit task scope.
- Record repeatable operations in this file instead of leaving them in chat history.
"""


def ensure_project_control_files(repo_root: Path, project_name: str, project_slug: str) -> dict[str, str]:
    shape = detect_project_shape(repo_root)
    renderers = {
        "PRODUCT_SPEC.md": lambda: render_product_spec(project_name, project_slug),
        "ARCHITECTURE.md": lambda: render_architecture(project_name, shape),
        "TASKS.md": render_tasks,
        "TESTING.md": lambda: render_testing(shape),
        "SECURITY.md": render_security,
        "DEPLOYMENT.md": lambda: render_deployment(shape),
        "OPERATIONS.md": render_operations,
    }
    results: dict[str, str] = {}
    for file_name in CONTROL_FILE_NAMES:
        path = repo_root / file_name
        if path.exists():
            results[file_name] = "exists"
            continue
        write_text(path, renderers[file_name]())
        results[file_name] = "created"
    return results


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
    parser.add_argument("--skip-control-files", action="store_true", help="只接入 wiki，不创建或更新项目级 AI 控制文件")
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
    control_results: dict[str, str] = {}
    if not args.skip_control_files:
        control_results.update(ensure_project_control_files(repo_root, project_name, project_slug))
        control_results["AGENTS.md"] = upsert_marked_block(
            repo_root / "AGENTS.md",
            render_managed_block("AGENTS.md", repo_root, wiki_root, project_slug),
        )
        control_results["CLAUDE.md"] = upsert_marked_block(
            repo_root / "CLAUDE.md",
            render_managed_block("CLAUDE.md", repo_root, wiki_root, project_slug),
        )

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
        f"repo_root: {repo_root} | wiki_root: {wiki_root} | project_slug: {project_slug} | user_config: {config_path} | control_files: {control_results or 'skipped'}",
    )
    subprocess.run([sys.executable, str(SCRIPT_DIR / "rebuild_indexes.py")], check=True, env=env)
    print(repo_root / "wiki.context.json")
    if control_results:
        for name, action in sorted(control_results.items()):
            print(f"{name}: {action}")


if __name__ == "__main__":
    main()
