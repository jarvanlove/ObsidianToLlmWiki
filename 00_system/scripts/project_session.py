from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


CONTROL_FILES = (
    "PRODUCT_SPEC.md",
    "ARCHITECTURE.md",
    "TASKS.md",
    "TESTING.md",
    "SECURITY.md",
    "DEPLOYMENT.md",
    "OPERATIONS.md",
    "CHANGELOG.md",
)

REQUIRED_SUPPORT_DIRECTORIES = ("docs/adr", "docs/ai-workflows", "scripts/ai")

WIKI_CORE_KEYS = (
    "project_index",
    "project_overview",
    "project_architecture",
    "project_decisions",
    "project_tasks",
    "project_risks",
    "project_timeline",
    "project_memory",
)


def load_context(repo_root: Path) -> dict[str, object]:
    context_path = repo_root / "wiki.context.json"
    if not context_path.exists():
        return {}
    try:
        payload = json.loads(context_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def git_output(repo_root: Path, args: list[str]) -> str:
    try:
        completed = subprocess.run(
            ["git", "-c", "core.quotepath=false", *args],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError:
        return ""
    return completed.stdout.rstrip("\r\n")


def changed_files(repo_root: Path) -> list[str]:
    names = {line.strip() for line in git_output(repo_root, ["diff", "--name-only", "HEAD"]).splitlines() if line.strip()}
    status_output = git_output(repo_root, ["status", "--short"])
    for line in status_output.splitlines():
        item = line[3:].strip()
        if " -> " in item:
            item = item.split(" -> ", 1)[1]
        if item:
            names.add(item)
    return sorted(names)


def has_any(paths: list[str], tokens: tuple[str, ...]) -> bool:
    lowered = [path.lower().replace("\\", "/") for path in paths]
    return any(any(token in path for token in tokens) for path in lowered)


def classify_update_candidates(paths: list[str]) -> list[str]:
    candidates = ["TASKS.md: update task status, blockers, verification, and follow-up."]
    if not paths:
        return candidates + ["No git changes detected; confirm whether this is a planning-only session."]

    if has_any(paths, ("readme", "product", "copy", "onboarding", "docs/product")):
        candidates.append("PRODUCT_SPEC.md: check whether user-facing scope or acceptance changed.")
    if has_any(paths, ("architecture", "docs/adr", "api", "schema", "model", "service", "adapter", "migration")):
        candidates.append("ARCHITECTURE.md or docs/adr/: check whether boundaries, contracts, or data flow changed.")
    if has_any(paths, ("test", "spec", "playwright", "pytest", "vitest", "jest", "testing.md")):
        candidates.append("TESTING.md: check whether verification commands or required checks changed.")
    if has_any(paths, ("auth", "security", "permission", "secret", "token", "login", "session")):
        candidates.append("SECURITY.md: check whether trust boundaries or sensitive rules changed.")
    if has_any(paths, ("deploy", "docker", "compose", "ci", "github/workflows", "env", "terraform", "helm")):
        candidates.append("DEPLOYMENT.md: check whether deploy steps, env vars, or rollback changed.")
    if has_any(paths, ("ops", "runbook", "monitor", "log", "health", "backup", "restore")):
        candidates.append("OPERATIONS.md: check whether diagnostics or incident handling changed.")
    if has_any(paths, ("changelog", "release", "version", "readme", "ui", "api", "feature")):
        candidates.append("CHANGELOG.md: check whether the diff is user-visible or release-level.")
    return candidates


def project_state(repo_root: Path) -> dict[str, Any]:
    context = load_context(repo_root)
    control_files = {file_name: "ok" if (repo_root / file_name).exists() else "missing" for file_name in CONTROL_FILES}
    support_directories = {
        dir_name: "ok" if (repo_root / dir_name).exists() else "missing"
        for dir_name in REQUIRED_SUPPORT_DIRECTORIES
    }
    wiki_pages: dict[str, str] = {}
    if context:
        wiki_root = Path(str(context.get("wiki_root") or ""))
        for key in WIKI_CORE_KEYS:
            rel = str(context.get(key) or "")
            wiki_pages[key] = "ok" if rel and (wiki_root / rel).exists() else "missing"
    missing_required = []
    if not context:
        missing_required.append("wiki.context.json")
    missing_required.extend(name for name, status in control_files.items() if status != "ok")
    missing_required.extend(name for name, status in support_directories.items() if status != "ok")
    missing_required.extend(key for key, status in wiki_pages.items() if status != "ok")
    changed = changed_files(repo_root)
    cockpit_state = "not_attached" if not context else "needs_close" if changed else "attached_idle"
    return {
        "repo_root": str(repo_root),
        "wiki_root": str(context.get("wiki_root") or "") if context else "",
        "project_slug": str(context.get("project_slug") or "") if context else "",
        "wiki_context": "ok" if context else "missing_or_invalid",
        "cockpit_state": cockpit_state,
        "changed_files": changed,
        "missing_required": missing_required,
        "control_files": control_files,
        "support_directories": support_directories,
        "wiki_core_pages": wiki_pages,
    }


def start_report(repo_root: Path, task: str) -> dict[str, Any]:
    return {
        "kind": "task_start",
        "state": project_state(repo_root),
        "task": task.strip() or "Read TASKS.md and select the next actionable task.",
        "checklist": [
            "classify: normal task / requirement change / bug fix / release check / operations incident",
            "risk: P3 docs/UI, P2 normal feature, P1 auth/core flow, P0 data deletion/payment/migration/security",
            "define acceptance before editing",
            "list expected touched files before editing",
            "choose the smallest relevant verification from TESTING.md",
        ],
    }


def close_report(repo_root: Path, verification: str) -> dict[str, Any]:
    paths = changed_files(repo_root)
    return {
        "kind": "task_close",
        "changed_files": paths,
        "verification": verification.strip() or "TODO: record exact commands and results.",
        "control_file_update_candidates": classify_update_candidates(paths),
        "wiki_file_back_candidates": [
            "Project decisions: durable requirement, architecture, or tradeoff decisions.",
            "Project risks: security, deployment, data, cost, or operational risks.",
            "Project timeline: releases, milestones, incidents.",
            "30_shared: cross-project workflow or reusable implementation pattern.",
            "10_personal: personal preference, habit, or recurring working method.",
        ],
        "rule": "do not write wiki for routine code edits without a durable conclusion.",
    }


def render_check_text(report: dict[str, Any]) -> str:
    lines = ["Project session check", f"- repo_root: {report['repo_root']}"]
    lines.append(f"- cockpit_state: {report.get('cockpit_state', 'unknown')}")
    if report["wiki_context"] == "ok":
        lines.extend([f"- wiki_root: {report['wiki_root']}", f"- project_slug: {report['project_slug']}"])
    else:
        lines.append("- wiki_context: missing or invalid")

    changed = report.get("changed_files") or []
    if changed:
        lines.append("\nChanged files")
        lines.extend(f"- {path}" for path in changed)

    missing_required = report.get("missing_required") or []
    if missing_required:
        lines.append("\nMissing required items")
        lines.extend(f"- {item}" for item in missing_required)

    lines.append("\nControl files")
    for file_name in CONTROL_FILES:
        status = report["control_files"][file_name]
        lines.append(f"- {file_name}: {status}")

    lines.append("\nSupport directories")
    for dir_name, status in report["support_directories"].items():
        lines.append(f"- {dir_name}: {status}")

    if report["wiki_core_pages"]:
        lines.append("\nWiki core pages")
        for key, status in report["wiki_core_pages"].items():
            lines.append(f"- {key}: {status}")
    return "\n".join(lines)


def render_start_text(report: dict[str, Any]) -> str:
    lines = [render_check_text(report["state"]), "\nTask start checklist", f"- task: {report['task']}"]
    lines.extend(f"- {item}" for item in report["checklist"])
    return "\n".join(lines)


def render_close_text(report: dict[str, Any]) -> str:
    lines = ["Task close checklist", "\nChanged files"]
    changed = report["changed_files"]
    lines.extend(f"- {path}" for path in changed) if changed else lines.append("- none detected")
    lines.extend(["\nVerification", f"- {report['verification']}", "\nControl file update candidates"])
    lines.extend(f"- {item}" for item in report["control_file_update_candidates"])
    lines.append("\nWiki file-back candidates")
    lines.extend(f"- {item}" for item in report["wiki_file_back_candidates"])
    lines.extend(["", f"Rule: {report['rule']}"])
    return "\n".join(lines)


def render_markdown(report: dict[str, Any]) -> str:
    if report.get("kind") == "task_start":
        return "# AI Task Start Report\n\n" + render_start_text(report) + "\n"
    if report.get("kind") == "task_close":
        return "# AI Task Close Report\n\n" + render_close_text(report) + "\n"
    return "# Project Session Check\n\n" + render_check_text(report) + "\n"


def write_or_print(content: str, output: str) -> None:
    if output.strip():
        path = Path(output).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.rstrip() + "\n", encoding="utf-8")
        print(path)
    else:
        print(content)


def main() -> None:
    parser = argparse.ArgumentParser(description="Check or close an ObsidianToWiki AI coding session.")
    parser.add_argument("command", choices=["check", "start", "close"])
    parser.add_argument("--repo-root", default=".", help="Project repository root.")
    parser.add_argument("--task", default="", help="Task description for start.")
    parser.add_argument("--verification", default="", help="Verification summary for close.")
    parser.add_argument("--strict", action="store_true", help="Exit with code 1 when required attach items are missing.")
    parser.add_argument("--format", choices=["text", "json", "markdown"], default="text", help="Output format.")
    parser.add_argument("--output", default="", help="Optional output file.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    if args.command == "check":
        report = project_state(repo_root)
    elif args.command == "start":
        report = start_report(repo_root, args.task)
    else:
        report = close_report(repo_root, args.verification)

    if args.format == "json":
        write_or_print(json.dumps(report, ensure_ascii=False, indent=2), args.output)
    elif args.format == "markdown":
        write_or_print(render_markdown(report), args.output)
    elif args.command == "check":
        write_or_print(render_check_text(report), args.output)
    elif args.command == "start":
        write_or_print(render_start_text(report), args.output)
    else:
        write_or_print(render_close_text(report), args.output)

    if args.strict and report.get("missing_required"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
