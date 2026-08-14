from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from engineering_governance import (
    TASK_STATE_REL_PATH,
    build_explanation_package,
    capture_git_baseline,
    create_task_state,
    evaluate_understanding_gate,
    load_task_state as load_governed_task_state,
    record_human_understanding,
    resume_summary,
    save_task_state,
    transition_task,
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
EVIDENCE_SOURCES = {"deterministic", "ai_self_check", "independent_ai_review", "human_observation"}
EVIDENCE_RESULTS = {"passed", "failed"}
EVIDENCE_FIELDS = ("kind", "command", "exit_code", "result", "recorded_at", "source")
MAX_EVIDENCE_ITEMS = 50
MAX_EVIDENCE_FILE_BYTES = 1_000_000


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


def load_receipt(path: Path, *, migrate_legacy: bool = True) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"status": "invalid"}
    if not isinstance(payload, dict):
        return {"status": "invalid"}
    if migrate_legacy and payload.get("schema_version") == 1:
        migrated = dict(payload)
        migrated.update(
            {
                "schema_version": 2,
                "legacy_schema_version": 1,
                "legacy_status": str(payload.get("status") or ""),
                "status": "blocked",
                "evidence": [],
                "gate_results": {
                    "verification_evidence": {"status": "blocked", "reasons": ["legacy_unstructured"]}
                },
                "explanation_package": {},
            }
        )
        return migrated
    return payload


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
        legacy = load_receipt(repo_root / TASK_STATE_REL_PATH, migrate_legacy=False)
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
    stored_candidates = [dict(item) for item in state.get("knowledge_candidates", []) if isinstance(item, dict)]
    task = str(report.get("task") or state.get("task") or "").strip()
    task_id = str(report.get("task_id") or state.get("task_id") or "").strip()
    gate_results = report.get("gate_results") if isinstance(report.get("gate_results"), dict) else {}
    verification_gate = gate_results.get("verification_evidence") if isinstance(gate_results.get("verification_evidence"), dict) else {}
    understanding_gate = gate_results.get("human_understanding") if isinstance(gate_results.get("human_understanding"), dict) else {}
    gates_passed = (
        task
        and task_id
        and verification_gate.get("status") == "passed"
        and understanding_gate.get("status") == "passed"
    )
    candidates = [
        candidate
        for candidate in stored_candidates
        if candidate.get("kind") != "capability_observation" or gates_passed
    ]
    if gates_passed:
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


def parse_evidence_inputs(repo_root: Path, raw_items: list[str], evidence_file: str = "") -> list[dict[str, Any]]:
    items: list[Any] = []
    if evidence_file.strip():
        path = Path(evidence_file).expanduser()
        if not path.is_absolute():
            path = repo_root / path
        try:
            if path.stat().st_size > MAX_EVIDENCE_FILE_BYTES:
                raise ValueError("evidence file exceeds 1000000 bytes")
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid evidence file: {path}") from exc
        if isinstance(payload, dict) and isinstance(payload.get("evidence"), list):
            items.extend(payload["evidence"])
        elif isinstance(payload, list):
            items.extend(payload)
        else:
            raise ValueError("evidence file must contain a JSON list or an object with an evidence list")
    for raw in raw_items:
        try:
            items.append(json.loads(raw))
        except json.JSONDecodeError as exc:
            raise ValueError("--evidence must be a JSON object") from exc
    if not all(isinstance(item, dict) for item in items):
        raise ValueError("every evidence item must be a JSON object")
    if len(items) > MAX_EVIDENCE_ITEMS:
        raise ValueError(f"evidence is limited to {MAX_EVIDENCE_ITEMS} items")
    return [dict(item) for item in items]


def evaluate_evidence(evidence: list[dict[str, Any]], risk_level: str, legacy_verification: str = "") -> dict[str, Any]:
    reasons: list[str] = []
    normalized: list[dict[str, Any]] = []
    if not evidence:
        reasons.append("legacy_unstructured" if legacy_verification.strip() else "structured_evidence_required")
    for index, item in enumerate(evidence):
        missing = [field for field in EVIDENCE_FIELDS if field not in item]
        if missing:
            reasons.append(f"evidence_{index}_missing_fields:" + ",".join(missing))
            continue
        selected = {
            "kind": str(item["kind"]).strip(),
            "command": str(item["command"]).strip(),
            "exit_code": item["exit_code"],
            "result": str(item["result"]).strip(),
            "recorded_at": str(item["recorded_at"]).strip(),
            "source": str(item["source"]).strip(),
        }
        if not selected["kind"] or not selected["command"]:
            reasons.append(f"evidence_{index}_identity_required")
        if isinstance(selected["exit_code"], bool) or not isinstance(selected["exit_code"], int):
            reasons.append(f"evidence_{index}_exit_code_must_be_integer")
        if selected["result"] not in EVIDENCE_RESULTS:
            reasons.append(f"evidence_{index}_invalid_result")
        if selected["source"] not in EVIDENCE_SOURCES:
            reasons.append(f"evidence_{index}_invalid_source")
        try:
            raw_recorded_at = str(selected["recorded_at"])
            if raw_recorded_at.endswith("Z"):
                raw_recorded_at = raw_recorded_at[:-1] + "+00:00"
            recorded_at = re.sub(
                r"(\.\d{6})\d+(?=(?:[+-]\d{2}:\d{2})?$)",
                r"\1",
                raw_recorded_at,
            )
            datetime.fromisoformat(recorded_at)
        except ValueError:
            reasons.append(f"evidence_{index}_invalid_recorded_at")
        if selected["result"] == "passed" and selected["exit_code"] != 0:
            reasons.append("passed_evidence_has_nonzero_exit_code")
        normalized.append(selected)
    passed = [item for item in normalized if item["result"] == "passed" and item["exit_code"] == 0]
    if evidence and not passed:
        reasons.append("passing_evidence_required")
    if risk_level in {"P0", "P1"} and passed and all(item["source"] == "ai_self_check" for item in passed):
        reasons.append("independent_evidence_required")
    unique_reasons = list(dict.fromkeys(reasons))
    return {
        "evidence": normalized,
        "gate": {"status": "blocked" if unique_reasons else "passed", "reasons": unique_reasons},
    }


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
    raw_evidence = report.get("evidence") if isinstance(report.get("evidence"), list) else []
    evidence_result = evaluate_evidence(
        [dict(item) for item in raw_evidence if isinstance(item, dict)],
        risk_level,
        str(report.get("verification") or ""),
    )
    explanation_package = build_explanation_package(
        repo_root,
        changed_files=[str(item) for item in report.get("changed_files", [])],
        evidence=evidence_result["evidence"],
        risk_level=risk_level,
    )
    understanding_gate = evaluate_understanding_gate(
        repo_root,
        explanation_package,
        risk_level=risk_level,
    )
    gate_results = {
        "verification_evidence": evidence_result["gate"],
        "human_understanding": understanding_gate,
    }
    verification = str(report.get("verification") or "").strip()
    if not verification and evidence_result["evidence"]:
        verification = "; ".join(
            f"{item['kind']}: {item['result']} ({item['command']})" for item in evidence_result["evidence"]
        )
    candidate_report = {**report, "task_id": task_id, "gate_results": gate_results}
    return {
        "schema_version": 2,
        "status": "pending"
        if all(gate.get("status") == "passed" for gate in gate_results.values())
        else "blocked",
        "created_at": created_at,
        "task_id": task_id,
        "task": task_summary,
        "repo_root": str(repo_root),
        "verification": verification,
        "evidence": evidence_result["evidence"],
        "gate_results": gate_results,
        "explanation_package": explanation_package,
        "risk": {"level": risk_level},
        "changed_files": report["changed_files"],
        "knowledge_candidates": _automatic_candidates(repo_root, candidate_report),
        "candidates": candidates,
    }


def resolve_receipt(path: Path, resolutions: list[str]) -> dict[str, Any]:
    receipt = load_receipt(path)
    if not receipt or receipt.get("status") == "invalid":
        raise SystemExit(f"invalid or missing session receipt: {path}")
    verification_gate = (receipt.get("gate_results") or {}).get("verification_evidence") or {}
    if verification_gate.get("status") != "passed":
        raise SystemExit("session receipt verification evidence gate is blocked")
    understanding_gate = (receipt.get("gate_results") or {}).get("human_understanding") or {}
    if understanding_gate.get("status") != "passed":
        raise SystemExit("session receipt human understanding gate is blocked")
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


def confirm_receipt_understanding(
    repo_root: Path,
    path: Path,
    *,
    confirmed_by: str,
    understood_impact_and_remaining_risks: bool,
    explicit_authorization: bool = False,
    confirmation_source: str,
) -> dict[str, Any]:
    receipt = load_receipt(path)
    if not receipt or receipt.get("status") in {"invalid", "resolved"}:
        raise SystemExit(f"receipt must be blocked or pending before confirmation: {path}")
    package = receipt.get("explanation_package")
    if not isinstance(package, dict):
        raise SystemExit("session receipt has no explanation package")
    risk_level = str((receipt.get("risk") or {}).get("level") or "P2").upper()
    record_human_understanding(
        repo_root,
        package,
        confirmed_by=confirmed_by,
        understood_impact_and_remaining_risks=understood_impact_and_remaining_risks,
        explicit_authorization=explicit_authorization,
        confirmation_source=confirmation_source,
    )
    gate = evaluate_understanding_gate(repo_root, package, risk_level=risk_level)
    receipt["gate_results"] = {**dict(receipt.get("gate_results") or {}), "human_understanding": gate}
    verification_gate = (receipt.get("gate_results") or {}).get("verification_evidence") or {}
    receipt["status"] = "pending" if verification_gate.get("status") == "passed" and gate["status"] == "passed" else "blocked"
    if receipt["status"] == "pending":
        receipt["knowledge_candidates"] = _automatic_candidates(repo_root, receipt)
        state = load_task_state(repo_root)
        if state.get("status") == "awaiting_understanding":
            transition_task(repo_root, "ready_to_close", reason="human understanding gate passed")
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
    if receipt["governance_status"] == "closed":
        state = load_task_state(repo_root)
        if str(state.get("task_id") or "") == str(receipt.get("task_id") or ""):
            if state.get("status") == "verifying":
                transition_task(repo_root, "ready_to_close", reason="verification and human understanding gates passed")
                state = load_task_state(repo_root)
            if state.get("status") == "ready_to_close":
                transition_task(repo_root, "closed", reason="session receipt resolved")
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
        else "blocked_verification"
        if receipt_status == "blocked"
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
    verification_gate = (receipt.get("gate_results") or {}).get("verification_evidence") or {}
    understanding_gate = (receipt.get("gate_results") or {}).get("human_understanding")
    understanding_passed = (
        understanding_gate.get("status") == "passed"
        if isinstance(understanding_gate, dict)
        else receipt.get("status") == "resolved"
    )
    return (
        receipt.get("status") == "resolved"
        and verification_gate.get("status") == "passed"
        and understanding_passed
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


def close_report(
    repo_root: Path,
    verification: str,
    ui_task: str = "",
    task: str = "",
    evidence: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    paths = changed_files(repo_root)
    state = load_task_state(repo_root)
    report: dict[str, Any] = {
        "kind": "task_close",
        "changed_files": paths,
        "verification": verification.strip(),
        "evidence": list(evidence or []),
        "task": task.strip() or str(state.get("task") or "").strip(),
        "task_id": str(state.get("task_id") or "").strip(),
        "risk": dict(state.get("risk") or {"level": "P2"}),
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
    package = report.get("explanation_package") or {}
    if package:
        labels = {
            "what_changed": "What changed",
            "why_changed": "Why",
            "data_or_call_chain_changes": "Data or call-chain change",
            "affected_files_and_boundaries": "Affected files and boundaries",
            "verification": "Verification evidence",
            "remaining_risks": "Remaining risks",
            "rollback": "Rollback",
        }
        lines.append("\nCritical-change explanation")
        for field, label in labels.items():
            lines.append(f"- {label}: {package.get(field, 'unknown')}")
    understanding_gate = (report.get("gate_results") or {}).get("human_understanding") or {}
    if understanding_gate:
        lines.append(f"- Human understanding gate: {understanding_gate.get('status', 'unknown')}")
        for reason in understanding_gate.get("reasons", []):
            lines.append(f"  - {reason}")
    if report.get("receipt_path"):
        lines.append(f"Receipt: {report['receipt_path']}")
        if report.get("receipt_status") == "blocked":
            lines.append("Structured verification evidence is blocked; record valid evidence and close again.")
        else:
            lines.append("Resolve every receipt candidate before reporting the session closed.")
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
    parser.add_argument("command", choices=["check", "start", "close", "understand", "resolve"])
    parser.add_argument("--repo-root", default=".", help="Project repository root.")
    parser.add_argument("--task", default="", help="Task description for start.")
    parser.add_argument("--verification", default="", help="Verification summary for close.")
    parser.add_argument("--evidence", action="append", default=[], help="Structured verification evidence as a JSON object; repeatable.")
    parser.add_argument("--evidence-file", default="", help="JSON file containing an evidence list or an object with an evidence list.")
    parser.add_argument("--ui-task", default="", help="Optional project-local UI task id that must pass visual evidence gates.")
    parser.add_argument("--strict", action="store_true", help="Exit with code 1 when required attach items are missing.")
    parser.add_argument("--format", choices=["text", "json", "markdown"], default="text", help="Output format.")
    parser.add_argument("--output", default="", help="Optional output file.")
    parser.add_argument("--receipt", default="", help="Optional session receipt path.")
    parser.add_argument("--confirmed-by", default="", help="Accountable human who confirmed the explanation package.")
    parser.add_argument(
        "--understood-impact-and-risks",
        action="store_true",
        help="Record the human's explicit understanding of impact and remaining risks.",
    )
    parser.add_argument(
        "--explicit-authorization",
        action="store_true",
        help="Record the additional explicit authorization required for P0.",
    )
    parser.add_argument("--confirmation-source", default="", help="Must be human; AI self-confirmation is rejected.")
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
            evidence = parse_evidence_inputs(repo_root, args.evidence, args.evidence_file)
            report = close_report(repo_root, args.verification, args.ui_task, args.task, evidence)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        target_receipt = receipt_path(repo_root, args.receipt)
        existing_receipt = load_receipt(target_receipt)
        if existing_receipt.get("status") in {"pending", "invalid"}:
            raise SystemExit(f"resolve the existing session receipt before closing again: {target_receipt}")
        receipt = build_receipt(repo_root, report)
        write_json_atomic(target_receipt, receipt)
        understanding_gate = (receipt.get("gate_results") or {}).get("human_understanding") or {}
        state = load_task_state(repo_root)
        if understanding_gate.get("status") == "blocked" and state.get("status") == "verifying":
            transition_task(repo_root, "awaiting_understanding", reason="human understanding confirmation required")
        report["verification"] = receipt["verification"] or "TODO: record structured verification evidence."
        report["receipt_path"] = str(target_receipt)
        report["receipt_status"] = receipt["status"]
        report["explanation_package"] = receipt["explanation_package"]
        report["gate_results"] = receipt["gate_results"]
    elif args.command == "understand":
        target_receipt = receipt_path(repo_root, args.receipt)
        try:
            report = confirm_receipt_understanding(
                repo_root,
                target_receipt,
                confirmed_by=args.confirmed_by,
                understood_impact_and_remaining_risks=args.understood_impact_and_risks,
                explicit_authorization=args.explicit_authorization,
                confirmation_source=args.confirmation_source,
            )
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
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
        or report.get("status") == "blocked"
        or report.get("governance_status") == "blocked_memory_repair"
    ):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
