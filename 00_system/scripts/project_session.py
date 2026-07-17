from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from datetime import datetime
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

REQUIRED_SUPPORT_DIRECTORIES = ("docs/adr", "docs/ai-workflows")

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

RECEIPT_REL_PATH = Path(".obsidiantowiki/session-receipt.json")
RESOLUTION_STATUSES = {"applied", "skipped", "not_applicable"}


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
    if has_any(paths, ("docs/design", "design/", "ui/", "component", "token", "theme", "css", "scss", "tailwind")):
        candidates.append("docs/design/UI_CONTRACT.md: check UI task evidence, approved design sources, and design-system impact.")
    if has_any(paths, ("auth", "security", "permission", "secret", "token", "login", "session")):
        candidates.append("SECURITY.md: check whether trust boundaries or sensitive rules changed.")
    if has_any(paths, ("deploy", "docker", "compose", "ci", "github/workflows", "env", "terraform", "helm")):
        candidates.append("DEPLOYMENT.md: check whether deploy steps, env vars, or rollback changed.")
    if has_any(paths, ("ops", "runbook", "monitor", "log", "health", "backup", "restore")):
        candidates.append("OPERATIONS.md: check whether diagnostics or incident handling changed.")
    if has_any(paths, ("changelog", "release", "version", "readme", "ui", "api", "feature")):
        candidates.append("CHANGELOG.md: check whether the diff is user-visible or release-level.")
    return candidates


def receipt_path(repo_root: Path, explicit: str = "") -> Path:
    return Path(explicit).expanduser().resolve() if explicit.strip() else repo_root / RECEIPT_REL_PATH


def load_receipt(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"status": "invalid"}
    return payload if isinstance(payload, dict) else {"status": "invalid"}


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temp_name, path)
    finally:
        temporary = Path(temp_name)
        if temporary.exists():
            temporary.unlink()


def build_receipt(repo_root: Path, report: dict[str, Any]) -> dict[str, Any]:
    candidates: list[dict[str, str]] = []
    for recommendation in report["control_file_update_candidates"]:
        target = recommendation.split(":", 1)[0]
        candidate_id = target if target.endswith(".md") else "session_assessment"
        candidates.append(
            {
                "id": f"control:{candidate_id}",
                "category": "control_file",
                "target": target,
                "recommendation": recommendation,
                "status": "pending",
            }
        )
    wiki_targets = (
        ("project_decisions", "Project decisions"),
        ("project_risks", "Project risks"),
        ("project_timeline", "Project timeline"),
        ("shared", "30_shared"),
        ("personal", "10_personal"),
    )
    for (candidate_id, target), recommendation in zip(wiki_targets, report["wiki_file_back_candidates"]):
        candidates.append(
            {
                "id": f"wiki:{candidate_id}",
                "category": "wiki_file_back",
                "target": target,
                "recommendation": recommendation,
                "status": "pending",
            }
        )
    return {
        "schema_version": 1,
        "status": "pending",
        "created_at": datetime.now().astimezone().replace(microsecond=0).isoformat(),
        "repo_root": str(repo_root),
        "verification": report["verification"],
        "changed_files": report["changed_files"],
        "candidates": candidates,
    }


def resolve_receipt(path: Path, resolutions: list[str]) -> dict[str, Any]:
    receipt = load_receipt(path)
    if not receipt or receipt.get("status") == "invalid":
        raise SystemExit(f"invalid or missing session receipt: {path}")
    candidates = receipt.get("candidates")
    if not isinstance(candidates, list):
        raise SystemExit(f"session receipt has no candidates: {path}")
    by_id = {str(item.get("id") or ""): item for item in candidates if isinstance(item, dict)}
    for raw in resolutions:
        candidate_id, separator, status = raw.partition("=")
        if not separator or candidate_id not in by_id:
            raise SystemExit(f"unknown receipt resolution: {raw}")
        if status not in RESOLUTION_STATUSES:
            raise SystemExit(f"invalid receipt status in {raw}; use applied, skipped, or not_applicable")
        by_id[candidate_id]["status"] = status
    pending = [candidate_id for candidate_id, item in by_id.items() if item.get("status") == "pending"]
    receipt["status"] = "pending" if pending else "resolved"
    receipt["resolved_at"] = "" if pending else datetime.now().astimezone().replace(microsecond=0).isoformat()
    receipt["pending_candidates"] = pending
    write_json_atomic(path, receipt)
    receipt["receipt_path"] = str(path)
    return receipt


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
    session_receipt = load_receipt(receipt_path(repo_root))
    receipt_status = str(session_receipt.get("status") or "none")
    receipt_candidates = session_receipt.get("candidates") if isinstance(session_receipt.get("candidates"), list) else []
    pending_candidates = [
        str(item.get("id") or "")
        for item in receipt_candidates
        if isinstance(item, dict) and item.get("status") == "pending"
    ]
    cockpit_state = (
        "not_attached"
        if not context
        else "needs_receipt_resolution"
        if receipt_status in {"pending", "invalid"}
        else "closed_pending_commit"
        if receipt_status == "resolved" and changed
        else "needs_close"
        if changed
        else "attached_idle"
    )
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
        "session_receipt": {
            "status": receipt_status,
            "path": str(receipt_path(repo_root)),
            "pending_candidates": pending_candidates,
        },
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


def close_report(repo_root: Path, verification: str, ui_task: str = "") -> dict[str, Any]:
    paths = changed_files(repo_root)
    report: dict[str, Any] = {
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
    if ui_task.strip():
        from ui_governance import validate_task

        ui_report = validate_task(repo_root, ui_task.strip(), phase="close")
        report["ui_governance"] = ui_report
        if not ui_report["passed"]:
            raise ValueError("UI task cannot close: " + "; ".join(ui_report["blocking"]))
    return report


def render_check_text(report: dict[str, Any]) -> str:
    lines = ["Project session check", f"- repo_root: {report['repo_root']}"]
    lines.append(f"- cockpit_state: {report.get('cockpit_state', 'unknown')}")
    receipt = report.get("session_receipt") or {}
    lines.append(f"- session_receipt: {receipt.get('status', 'none')}")
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
    if report.get("receipt_path"):
        lines.extend([f"Receipt: {report['receipt_path']}", "Resolve every receipt candidate before reporting the session closed."])
    return "\n".join(lines)


def render_receipt_text(report: dict[str, Any]) -> str:
    lines = [f"Session receipt: {report['status']}", f"- path: {report['receipt_path']}"]
    for candidate in report.get("candidates", []):
        lines.append(f"- {candidate['id']}: {candidate['status']}")
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
    parser.add_argument("command", choices=["check", "start", "close", "resolve"])
    parser.add_argument("--repo-root", default=".", help="Project repository root.")
    parser.add_argument("--task", default="", help="Task description for start.")
    parser.add_argument("--verification", default="", help="Verification summary for close.")
    parser.add_argument("--ui-task", default="", help="Optional project-local UI task id that must pass visual evidence gates.")
    parser.add_argument("--strict", action="store_true", help="Exit with code 1 when required attach items are missing.")
    parser.add_argument("--format", choices=["text", "json", "markdown"], default="text", help="Output format.")
    parser.add_argument("--output", default="", help="Optional output file.")
    parser.add_argument("--receipt", default="", help="Optional session receipt path.")
    parser.add_argument(
        "--resolution",
        action="append",
        default=[],
        help="Resolve one candidate as id=applied|skipped|not_applicable; repeat for each candidate.",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    if args.command == "check":
        report = project_state(repo_root)
    elif args.command == "start":
        report = start_report(repo_root, args.task)
    elif args.command == "close":
        try:
            report = close_report(repo_root, args.verification, args.ui_task)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        target_receipt = receipt_path(repo_root, args.receipt)
        existing_receipt = load_receipt(target_receipt)
        if existing_receipt.get("status") in {"pending", "invalid"}:
            raise SystemExit(f"resolve the existing session receipt before closing again: {target_receipt}")
        receipt = build_receipt(repo_root, report)
        write_json_atomic(target_receipt, receipt)
        report["receipt_path"] = str(target_receipt)
        report["receipt_status"] = "pending"
    else:
        report = resolve_receipt(receipt_path(repo_root, args.receipt), args.resolution)

    if args.format == "json":
        write_or_print(json.dumps(report, ensure_ascii=False, indent=2), args.output)
    elif args.format == "markdown":
        write_or_print(render_markdown(report), args.output)
    elif args.command == "check":
        write_or_print(render_check_text(report), args.output)
    elif args.command == "start":
        write_or_print(render_start_text(report), args.output)
    elif args.command == "close":
        write_or_print(render_close_text(report), args.output)
    else:
        write_or_print(render_receipt_text(report), args.output)

    if args.strict and (report.get("missing_required") or report.get("status") == "pending"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
