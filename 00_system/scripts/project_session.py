from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from engineering_governance import (
    TASK_STATE_REL_PATH,
    capture_git_baseline,
    create_task_state,
    load_task_state as load_governed_task_state,
    resume_summary,
    save_task_state,
)


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


def load_task_state(repo_root: Path) -> dict[str, Any]:
    try:
        return load_governed_task_state(repo_root)
    except ValueError:
        legacy = load_receipt(repo_root / TASK_STATE_REL_PATH)
        if not (
            legacy.get("schema_version") == 1
            and legacy.get("status") == "active"
            and isinstance(legacy.get("task_id"), str)
            and str(legacy["task_id"]).strip()
            and isinstance(legacy.get("task"), str)
            and str(legacy["task"]).strip()
        ):
            raise
        state = create_task_state(repo_root, str(legacy["task"]), "code_change")
        state["task_id"] = str(legacy["task_id"])
        state["baseline"] = capture_git_baseline(repo_root)
        state["knowledge_candidates"] = [
            dict(item) for item in legacy.get("knowledge_candidates", []) if isinstance(item, dict)
        ]
        state["context_receipt"] = str(legacy.get("context_receipt") or "")
        state["migrated_from"] = "legacy_active"
        started_at = str(legacy.get("started_at") or "").strip()
        if started_at:
            state["timestamps"]["created_at"] = started_at
        save_task_state(repo_root, state)
        return state


def _initial_snapshot_candidate(repo_root: Path) -> dict[str, Any] | None:
    context = load_context(repo_root)
    if not context:
        return None
    wiki_root = Path(str(context.get("wiki_root") or ""))
    project_slug = str(context.get("project_slug") or "").strip()
    memory_dir = wiki_root / "20_projects" / "active" / project_slug / "memory"
    if project_slug and memory_dir.exists() and any(memory_dir.glob("*.md")):
        return None
    present = [name for name in CONTROL_FILES if (repo_root / name).exists()]
    if not present:
        return None
    return {
        "kind": "milestone",
        "stable_key": "initial-project-snapshot",
        "summary": f"Initial project snapshot: {len(present)} governed control files are present.",
        "evidence_refs": [f"git:{git_output(repo_root, ['rev-parse', 'HEAD']) or 'uncommitted'}", *[f"control:{name}" for name in present]],
        "destination": "project",
    }


def _automatic_candidates(repo_root: Path, report: dict[str, Any]) -> list[dict[str, Any]]:
    state = load_task_state(repo_root)
    candidates = [dict(item) for item in state.get("knowledge_candidates", []) if isinstance(item, dict)]
    task = str(report.get("task") or state.get("task") or "").strip()
    task_id = str(report.get("task_id") or state.get("task_id") or "").strip()
    verification = str(report.get("verification") or "").strip()
    if task and task_id and verification and not verification.startswith("TODO:"):
        candidates.append(
            {
                "kind": "milestone",
                "stable_key": task_id,
                "summary": f"Completed: {task}",
                "evidence_refs": [f"receipt:{task_id}", f"git:{git_output(repo_root, ['rev-parse', 'HEAD']) or 'uncommitted'}"],
                "destination": "project",
            }
        )
    unique: dict[tuple[str, str], dict[str, Any]] = {}
    for candidate in candidates:
        unique[(str(candidate.get("kind") or ""), str(candidate.get("stable_key") or ""))] = candidate
    return list(unique.values())


def memory_health(repo_root: Path) -> dict[str, Any]:
    context = load_context(repo_root)
    if not context:
        return {"status": "unavailable", "maintenance_reasons": ["wiki_context_missing"], "activity_state": "unknown", "recovery_summary": ""}
    from memory_compiler import CORE_PROJECTION_NAMES, PROJECTION_START, estimate_tokens, load_policy
    from wiki_lib import parse_frontmatter

    wiki_root = Path(str(context.get("wiki_root") or ""))
    project_slug = str(context.get("project_slug") or "").strip()
    project_root = wiki_root / "20_projects" / "active" / project_slug
    policy = load_policy()
    projections = policy.get("projections") if isinstance(policy.get("projections"), dict) else {}
    budgets = projections.get("page_token_budgets") if isinstance(projections.get("page_token_budgets"), dict) else {}
    reasons: list[str] = []
    unmanaged: list[str] = []
    for name in CORE_PROJECTION_NAMES:
        path = project_root / name
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8")
        if PROJECTION_START not in content:
            unmanaged.append(name)
        if estimate_tokens(content) > int(budgets.get(name) or 1000):
            reasons.append("projection_over_budget")
    if unmanaged:
        reasons.append("unmanaged_core_pages_require_migration")

    latest: date | None = None
    for path in sorted((project_root / "memory").glob("*.md")):
        try:
            frontmatter, _body = parse_frontmatter(path.read_text(encoding="utf-8"))
            effective = date.fromisoformat(str(frontmatter.get("effective_from") or ""))
        except (OSError, UnicodeError, ValueError):
            continue
        latest = max(latest, effective) if latest else effective
    cooled = bool(latest and latest < date.today() - timedelta(days=90))
    recovery = "项目已超过 90 天无活动；恢复时仅加载当前控制文件、开放风险和最近有效里程碑。" if cooled else ""
    return {
        "status": "needs_maintenance" if reasons else "current",
        "maintenance_reasons": list(dict.fromkeys(reasons)),
        "unmanaged_pages": unmanaged,
        "activity_state": "cooled" if cooled else "active",
        "recovery_summary": recovery,
    }


def _context_check(repo_root: Path, task: str, task_id: str) -> dict[str, Any]:
    context = load_context(repo_root)
    if not context:
        return {"status": "missing", "token_usage": {"limit": 6000, "used": 0}, "receipt_path": ""}
    try:
        from context_contract import build_context

        result = build_context(
            repo_root=repo_root,
            wiki_root=Path(str(context.get("wiki_root") or "")),
            query=task,
            task_id=task_id,
            candidates=[],
        )
    except (OSError, ValueError) as exc:
        return {"status": "missing", "token_usage": {"limit": 6000, "used": 0}, "receipt_path": "", "error": type(exc).__name__}
    return {
        "status": result["status"],
        "token_usage": result["token_usage"],
        "receipt_path": result["receipt_path"],
    }


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
    created_at = datetime.now().astimezone().replace(microsecond=0).isoformat()
    task_summary = str(report.get("task") or "").strip()
    state = load_task_state(repo_root)
    task_id = str(report.get("task_id") or state.get("task_id") or "").strip() or "session-" + hashlib.sha256(
        f"{repo_root}|{created_at}|{task_summary}".encode("utf-8")
    ).hexdigest()[:16]
    report_risk = report.get("risk") if isinstance(report.get("risk"), dict) else {}
    risk_level = str(report_risk.get("level") or "P2").upper()
    return {
        "schema_version": 1,
        "status": "pending",
        "created_at": created_at,
        "task_id": task_id,
        "task": task_summary,
        "repo_root": str(repo_root),
        "verification": report["verification"],
        "risk": {"level": risk_level},
        "changed_files": report["changed_files"],
        "knowledge_candidates": _automatic_candidates(repo_root, {**report, "task_id": task_id}),
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


def finalize_memory_maintenance(repo_root: Path, path: Path, receipt: dict[str, Any]) -> dict[str, Any]:
    if receipt.get("status") != "resolved":
        return receipt
    health = memory_health(repo_root)
    context = load_context(repo_root)
    maintenance: dict[str, Any]
    if "unmanaged_core_pages_require_migration" in health.get("maintenance_reasons", []):
        maintenance = {"status": "blocked", "reason": "unmanaged_core_pages_require_migration"}
        memory_status = "pending_memory_repair"
    elif not context:
        maintenance = {"status": "blocked", "reason": "wiki_context_missing"}
        memory_status = "pending_memory_repair"
    else:
        try:
            from memory_compiler import compile_projections, compile_receipt
            from project_cockpit import build_cockpit

            wiki_root = Path(str(context.get("wiki_root") or ""))
            project_slug = str(context.get("project_slug") or "")
            cards = compile_receipt(path, wiki_root=wiki_root, project_slug=project_slug)
            if cards.get("status") == "blocked":
                raise ValueError("memory_receipt_compile_blocked")
            projections = compile_projections(wiki_root=wiki_root, project_slug=project_slug)
            if projections.get("status") == "blocked":
                raise ValueError(str(projections.get("reason") or "projection_compile_blocked"))
            cockpit = build_cockpit(repo_root)
            maintenance = {
                "status": "completed",
                "cards": cards.get("status"),
                "projections": projections.get("status"),
                "cockpit": cockpit.get("status"),
            }
            memory_status = "current"
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            maintenance = {"status": "blocked", "reason": str(exc) or type(exc).__name__}
            memory_status = "pending_memory_repair"
    receipt["memory_status"] = memory_status
    receipt["memory_maintenance"] = maintenance
    if memory_status != "current" and str((receipt.get("risk") or {}).get("level") or "P2").upper() in {"P0", "P1"}:
        receipt["governance_status"] = "blocked_memory_repair"
    else:
        receipt["governance_status"] = "closed"
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
    try:
        engineering_state = load_task_state(repo_root)
        if engineering_state:
            recovery = resume_summary(repo_root)
            comparison = recovery.get("comparison") if isinstance(recovery.get("comparison"), dict) else {}
            baseline = comparison.get("baseline") if isinstance(comparison.get("baseline"), dict) else {}
            engineering_task = {
                "status": recovery["status"],
                "task_id": recovery["task_id"],
                "task": recovery["task"],
                "stale": bool(comparison.get("stale")),
                "stale_reasons": list(comparison.get("stale_reasons") or []),
                "preexisting_change_count": len(comparison.get("preexisting_changes") or []),
                "preexisting_tracked_count": len(baseline.get("tracked_modified") or []),
                "preexisting_untracked_count": len(baseline.get("untracked") or []),
                "task_changes": list(comparison.get("task_changes") or []),
            }
        else:
            engineering_task = {"status": "none", "task_id": "", "task": "", "stale": False}
    except ValueError as exc:
        engineering_task = {"status": "invalid", "task_id": "", "task": "", "stale": True, "error": str(exc)}
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
        "engineering_task": engineering_task,
    }


def _task_closed_by_receipt(repo_root: Path, state: dict[str, Any]) -> bool:
    if str(state.get("status") or "") in {"closed", "abandoned"}:
        return True
    receipt = load_receipt(receipt_path(repo_root))
    return (
        receipt.get("status") == "resolved"
        and receipt.get("governance_status") == "closed"
        and str(receipt.get("task_id") or "") == str(state.get("task_id") or "")
    )


def start_report(repo_root: Path, task: str) -> dict[str, Any]:
    previous = load_task_state(repo_root)
    requested_task = task.strip()
    previous_is_open = bool(previous) and not _task_closed_by_receipt(repo_root, previous)
    if previous_is_open:
        state = previous
        recovery = resume_summary(repo_root)
        state = load_task_state(repo_root)
        selected_task = str(state["task"])
        resumed = True
    else:
        selected_task = requested_task or "Read TASKS.md and select the next actionable task."
        baseline = capture_git_baseline(repo_root)
        state = create_task_state(repo_root, selected_task, "code_change")
        state["baseline"] = baseline
        recovery = {"status": state["status"], "task_id": state["task_id"], "task": state["task"], "comparison": {}}
        resumed = False
    task_id = str(state["task_id"])
    candidates = [dict(item) for item in state.get("knowledge_candidates", []) if isinstance(item, dict)]
    initial = _initial_snapshot_candidate(repo_root)
    if initial and not any(item.get("stable_key") == initial["stable_key"] for item in candidates):
        candidates.append(initial)
    health = memory_health(repo_root)
    context_check = _context_check(repo_root, selected_task, task_id)
    state["knowledge_candidates"] = candidates
    state["context_receipt"] = context_check.get("receipt_path", "")
    state["timestamps"]["updated_at"] = datetime.now().astimezone().replace(microsecond=0).isoformat()
    save_task_state(repo_root, state)
    return {
        "kind": "task_start",
        "state": project_state(repo_root),
        "task": selected_task,
        "requested_task": requested_task or selected_task,
        "task_id": task_id,
        "resumed": resumed,
        "recovery": recovery,
        "memory_lifecycle": {
            "context_status": context_check["status"],
            "token_usage": context_check["token_usage"],
            "candidate_count": len(candidates),
            "maintenance_reasons": health["maintenance_reasons"],
            "activity_state": health["activity_state"],
            "recovery_summary": health["recovery_summary"],
        },
        "checklist": [
            "classify: normal task / requirement change / bug fix / release check / operations incident",
            "risk: P3 docs/UI, P2 normal feature, P1 auth/core flow, P0 data deletion/payment/migration/security",
            "define acceptance before editing",
            "list expected touched files before editing",
            "choose the smallest relevant verification from TESTING.md",
        ],
    }


def close_report(repo_root: Path, verification: str, ui_task: str = "", task: str = "") -> dict[str, Any]:
    paths = changed_files(repo_root)
    state = load_task_state(repo_root)
    report: dict[str, Any] = {
        "kind": "task_close",
        "changed_files": paths,
        "verification": verification.strip() or "TODO: record exact commands and results.",
        "task": task.strip() or str(state.get("task") or "").strip(),
        "task_id": str(state.get("task_id") or "").strip(),
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

    engineering_task = report.get("engineering_task") or {}
    if engineering_task.get("status") not in {None, "", "none"}:
        lines.append("\nEngineering task")
        lines.append(f"- task: {engineering_task.get('task', '')}")
        lines.append(f"- status: {engineering_task.get('status', 'unknown')}")
        lines.append(f"- preexisting tracked changes: {engineering_task.get('preexisting_tracked_count', 0)}")
        lines.append(f"- preexisting untracked files: {engineering_task.get('preexisting_untracked_count', 0)}")
        task_changes = list(engineering_task.get("task_changes") or [])
        if task_changes:
            lines.append("- task changes: " + ", ".join(task_changes[:20]))
        if engineering_task.get("stale"):
            lines.append("- recovery required: " + ", ".join(engineering_task.get("stale_reasons") or ["unknown"]))

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
    lifecycle = report.get("memory_lifecycle") or {}
    usage = lifecycle.get("token_usage") or {}
    lines.append(f"- context: {lifecycle.get('context_status', 'unknown')} ({usage.get('used', 0)}/{usage.get('limit', 6000)} tokens)")
    if lifecycle.get("recovery_summary"):
        lines.append(f"- recovery: {lifecycle['recovery_summary']}")
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
            report = close_report(repo_root, args.verification, args.ui_task, args.task)
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
        target_receipt = receipt_path(repo_root, args.receipt)
        report = resolve_receipt(target_receipt, args.resolution)
        if report.get("status") == "resolved":
            report = finalize_memory_maintenance(repo_root, target_receipt, report)

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

    if args.strict and (
        report.get("missing_required")
        or report.get("status") == "pending"
        or report.get("governance_status") == "blocked_memory_repair"
    ):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
