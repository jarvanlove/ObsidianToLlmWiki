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
    for name in ("wiki_root", "source", "title", "question", "conclusion", "tags"):
        value = str(getattr(args, name, "") or "").strip()
        if value:
            values.extend([f"--{name.replace('_', '-')}", value])
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


if __name__ == "__main__":
    main()
