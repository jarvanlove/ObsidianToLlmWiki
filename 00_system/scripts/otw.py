from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from project_adapter import inspect_adapter
from wiki_lib import detect_wiki_root


SCRIPT_DIR = Path(__file__).resolve().parent
SOURCE_ROOT = SCRIPT_DIR.parent.parent


def run_script(name: str, args: list[str], *, env: dict[str, str] | None = None) -> None:
    subprocess.run([sys.executable, str(SCRIPT_DIR / name), *args], check=True, env=env)


def wiki_env(repo_root: Path, explicit_root: str) -> tuple[Path, dict[str, str]]:
    wiki_root = detect_wiki_root(repo_root=repo_root, explicit_root=explicit_root or None)
    env = dict(os.environ)
    env["OBSIDIAN_WIKI_ROOT"] = str(wiki_root)
    return wiki_root, env


def add_project_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo-root", default=".", help="Project repository root; defaults to the current directory.")
    parser.add_argument("--wiki-root", default="", help="Explicit private wiki root for first-time setup.")


def nl_args(args: argparse.Namespace, request: str) -> list[str]:
    values = ["--request", request, "--repo-root", str(Path(args.repo_root).expanduser().resolve())]
    for name in ("wiki_root", "source", "title", "question", "conclusion", "tags", "task", "ui_task"):
        value = str(getattr(args, name, "") or "").strip()
        if value:
            values.extend([f"--{name.replace('_', '-')}", value])
    for item in getattr(args, "evidence", []) or []:
        values.extend(["--evidence", str(item)])
    evidence_file = str(getattr(args, "evidence_file", "") or "").strip()
    if evidence_file:
        values.extend(["--evidence-file", evidence_file])
    return values


def run_natural_language(args: argparse.Namespace, request: str) -> None:
    run_script("handle_nl_request.py", nl_args(args, request))


def run_upgrade(args: argparse.Namespace) -> None:
    repo_root = Path(args.repo_root).expanduser().resolve()
    wiki_root, env = wiki_env(repo_root, args.wiki_root)
    if args.apply:
        run_script("vault_compat.py", ["migrate", "--apply"], env=env)
        run_script(
            "shared_assets.py",
            ["apply-safe", "--vault-root", str(wiki_root), "--source-root", str(SOURCE_ROOT)],
            env=env,
        )
        repo_roots = [repo_root]
        if args.all_projects:
            registry_path = wiki_root / "00_system" / "registry" / "projects.json"
            if registry_path.exists():
                payload = json.loads(registry_path.read_text(encoding="utf-8"))
                if isinstance(payload, list):
                    repo_roots = [
                        Path(str(item.get("project_repo_root") or "")).expanduser().resolve()
                        for item in payload
                        if isinstance(item, dict) and str(item.get("project_repo_root") or "").strip()
                    ]
        for candidate in dict.fromkeys(repo_roots):
            if not candidate.exists():
                continue
            run_script(
                "project_scaffold.py",
                ["--repo-root", str(candidate), "--source-root", str(SOURCE_ROOT)],
                env=env,
            )
            adapter = inspect_adapter(candidate)
            if adapter["status"] != "not_installed":
                run_script("project_adapter.py", ["apply", "--repo-root", str(candidate)], env=env)
    run_script("vault_compat.py", ["report"], env=env)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Unified ObsidianToWiki runtime. Agents should call this entrypoint for normal user workflows."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    ask = subparsers.add_parser("ask", help="Route a natural-language wiki request.")
    ask.add_argument("request")
    add_project_options(ask)
    ask.add_argument("--source", default="")
    ask.add_argument("--title", default="")
    ask.add_argument("--question", default="")
    ask.add_argument("--conclusion", default="")
    ask.add_argument("--tags", default="")

    for command in ("start", "continue", "close", "attach"):
        command_parser = subparsers.add_parser(command)
        add_project_options(command_parser)
        command_parser.add_argument("--verification", default="")
        if command in {"start", "continue"}:
            command_parser.add_argument("--task", default="")
        if command == "close":
            command_parser.add_argument("--ui-task", default="")
            command_parser.add_argument("--evidence", action="append", default=[])
            command_parser.add_argument("--evidence-file", default="")

    ui = subparsers.add_parser("ui", help="Run project-local UI governance checks for an agent-managed UI task.")
    ui.add_argument("action", choices=["assess", "init", "set-stage", "approve-rfc", "record-evidence", "check", "list-directions", "recommend-directions", "select-direction"])
    add_project_options(ui)
    ui.add_argument("--task", default="")
    ui.add_argument("--task-id", default="")
    ui.add_argument("--level", choices=["U0", "U1", "U2", "U3"], default="")
    ui.add_argument("--requested-skill", default="")
    ui.add_argument("--visual-direction", default="")
    ui.add_argument("--feedback", default="")
    ui.add_argument("--product-context", default="")
    ui.add_argument("--stage", default="")
    ui.add_argument("--approval-note", default="")
    ui.add_argument("--screenshot", action="append", default=[])
    ui.add_argument("--visual-qa", default="")
    ui.add_argument("--accessibility-report", action="append", default=[])
    ui.add_argument("--note", default="")
    ui.add_argument("--phase", choices=["implementation", "close"], default="implementation")
    ui.add_argument("--format", choices=["text", "json"], default="text")

    search = subparsers.add_parser("search")
    search.add_argument("query")
    add_project_options(search)
    search.add_argument("--project", default="")
    search.add_argument("--format", choices=["text", "json", "context"], default="context")

    ingest = subparsers.add_parser("ingest")
    ingest.add_argument("source")
    add_project_options(ingest)
    ingest.add_argument("--scope", choices=["personal", "project"], default="personal")
    ingest.add_argument("--title", default="")
    ingest.add_argument("--tags", default="")

    check = subparsers.add_parser("check")
    add_project_options(check)
    check.add_argument("--strict", action="store_true")

    context = subparsers.add_parser("context", help="Inspect required AI context without modifying project or wiki files.")
    context_subparsers = context.add_subparsers(dest="context_action", required=True)
    context_check = context_subparsers.add_parser("check")
    add_project_options(context_check)
    context_check.add_argument("--strict", action="store_true")
    context_check.add_argument("--format", choices=["text", "json"], default="text")

    memory = subparsers.add_parser("memory", help="Compile bounded memory projections or migrate legacy project pages.")
    memory_subparsers = memory.add_subparsers(dest="memory_action", required=True)
    memory_compile = memory_subparsers.add_parser("compile")
    add_project_options(memory_compile)
    memory_compile.add_argument("--dry-run", action="store_true")
    memory_migrate = memory_subparsers.add_parser("migrate")
    add_project_options(memory_migrate)
    migration_mode = memory_migrate.add_mutually_exclusive_group(required=True)
    migration_mode.add_argument("--dry-run", action="store_true")
    migration_mode.add_argument("--apply", action="store_true")

    cockpit = subparsers.add_parser("cockpit", help="Build or open the local human-first project cockpit.")
    cockpit.add_argument("action", choices=["build", "open"])
    add_project_options(cockpit)
    cockpit.add_argument("--format", choices=["text", "json"], default="text")

    resolve = subparsers.add_parser("resolve")
    add_project_options(resolve)
    resolve.add_argument("--resolution", action="append", required=True)
    resolve.add_argument("--strict", action="store_true")

    upgrade = subparsers.add_parser("upgrade")
    add_project_options(upgrade)
    upgrade.add_argument("--apply", action="store_true", help="Apply metadata and hash-safe upgrades; conflicts are staged.")
    upgrade.add_argument("--all-projects", action="store_true", help="Safely upgrade adapters already installed in registered projects.")

    doctor = subparsers.add_parser("doctor")
    add_project_options(doctor)
    doctor.add_argument("--strict", action="store_true")
    doctor.add_argument("--format", choices=["text", "json"], default="text")

    setup = subparsers.add_parser("setup", help="Initialize the private vault and install the manager Skill once.")
    setup.add_argument("--private-root", default="")
    setup.add_argument("--provider", choices=["agents", "claude", "all"], default="all")
    setup.add_argument("--format", choices=["text", "json"], default="text")

    update = subparsers.add_parser("update", help="Safely update runtime, private scaffold, Skills, and attached projects.")
    update.add_argument("--private-root", default="")
    update.add_argument("--provider", choices=["agents", "claude", "all"], default="all")
    update.add_argument("--check", action="store_true")
    update.add_argument("--format", choices=["text", "json"], default="text")

    args = parser.parse_args()
    if args.command == "ask":
        run_natural_language(args, args.request)
    elif args.command == "start":
        run_natural_language(args, "开始工作")
    elif args.command == "continue":
        run_natural_language(args, "继续")
    elif args.command == "close":
        args.conclusion = args.verification
        run_natural_language(args, "收工")
    elif args.command == "ui":
        values = [args.action, "--repo-root", str(Path(args.repo_root).expanduser().resolve()), "--format", args.format]
        for name in ("task", "task_id", "level", "requested_skill", "visual_direction", "feedback", "product_context", "stage", "approval_note", "visual_qa", "note", "phase"):
            value = str(getattr(args, name, "") or "").strip()
            if value:
                values.extend([f"--{name.replace('_', '-')}", value])
        for item in args.screenshot:
            values.extend(["--screenshot", item])
        for item in args.accessibility_report:
            values.extend(["--accessibility-report", item])
        run_script("ui_governance.py", values)
    elif args.command == "attach":
        run_natural_language(args, "将当前项目接入 wiki")
    elif args.command == "search":
        repo_root = Path(args.repo_root).expanduser().resolve()
        _wiki_root, env = wiki_env(repo_root, args.wiki_root)
        values = [args.query, "--format", args.format]
        if args.project:
            values.extend(["--project", args.project])
        run_script("search_wiki.py", values, env=env)
    elif args.command == "ingest":
        args.source = args.source
        request = "将资料摄入当前项目" if args.scope == "project" else "将资料摄入个人知识库"
        run_natural_language(args, request)
    elif args.command == "check":
        values = ["check", "--repo-root", str(Path(args.repo_root).expanduser().resolve())]
        if args.strict:
            values.append("--strict")
        run_script("project_session.py", values)
    elif args.command == "context":
        values = ["--repo-root", str(Path(args.repo_root).expanduser().resolve()), "--format", args.format]
        if args.strict:
            values.append("--strict")
        run_script("context_integrity.py", values)
    elif args.command == "memory":
        values = ["--repo-root", str(Path(args.repo_root).expanduser().resolve())]
        if args.memory_action == "compile":
            if args.dry_run:
                values.append("--dry-run")
            run_script("memory_compiler.py", values)
        else:
            values.append("--apply" if args.apply else "--dry-run")
            run_script("migrate_project_memory.py", values)
    elif args.command == "cockpit":
        run_script(
            "project_cockpit.py",
            [args.action, "--repo-root", str(Path(args.repo_root).expanduser().resolve()), "--format", args.format],
        )
    elif args.command == "resolve":
        values = ["resolve", "--repo-root", str(Path(args.repo_root).expanduser().resolve())]
        for resolution in args.resolution:
            values.extend(["--resolution", resolution])
        if args.strict:
            values.append("--strict")
        run_script("project_session.py", values)
    elif args.command == "upgrade":
        run_upgrade(args)
    elif args.command == "doctor":
        values = ["--repo-root", str(Path(args.repo_root).expanduser().resolve()), "--format", args.format]
        if args.wiki_root:
            values.extend(["--wiki-root", args.wiki_root])
        if args.strict:
            values.append("--strict")
        run_script("doctor.py", values)
    elif args.command in {"setup", "update"}:
        values = [args.command, "--source-root", str(SOURCE_ROOT), "--provider", args.provider, "--format", args.format]
        if args.private_root:
            values.extend(["--private-root", args.private_root])
        if args.command == "update" and args.check:
            values.append("--check")
        run_script("runtime_manager.py", values)


if __name__ == "__main__":
    main()
