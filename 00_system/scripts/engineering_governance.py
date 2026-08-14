from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any


REGISTRY_PATH = Path(__file__).resolve().parents[1] / "registry" / "engineering_governance.json"


def _load_registry() -> dict[str, Any]:
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("engineering governance registry must be an object")
    return payload


REGISTRY = _load_registry()
TASK_STATE_REL_PATH = Path(str(REGISTRY["task_state_path"]))
SCHEMA_VERSION = int(REGISTRY["schema_version"])
STATUSES = frozenset(str(item) for item in REGISTRY["statuses"])
RISK_LEVELS = frozenset(str(item) for item in REGISTRY["risk_levels"])
RISK_ORDER = tuple(str(item) for item in REGISTRY["risk_levels"])
RISK_RULES = tuple(dict(item) for item in REGISTRY["risk_rules"])
TRANSITIONS = {
    str(source): frozenset(str(target) for target in targets)
    for source, targets in dict(REGISTRY["transitions"]).items()
}


def _now() -> str:
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def _state_path(repo_root: Path) -> Path:
    return repo_root.resolve() / TASK_STATE_REL_PATH


def _task_id(task: str, created_at: str) -> str:
    words = re.findall(r"[a-z0-9]+", task.lower())[:4]
    slug = "-".join(words) or "task"
    digest = hashlib.sha256(f"{created_at}|{task}".encode("utf-8")).hexdigest()[:8]
    compact_time = re.sub(r"[^0-9T]", "", created_at.split("+", 1)[0]).replace("-", "").replace(":", "")
    return f"{compact_time}-{slug}-{digest}"


def _validate_state(state: dict[str, Any]) -> None:
    if not isinstance(state, dict):
        raise ValueError("task state must be an object")
    if state.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"unsupported task state schema: {state.get('schema_version')!r}")
    if not isinstance(state.get("task_id"), str) or not str(state["task_id"]).strip():
        raise ValueError("task state requires task_id")
    status = str(state.get("status") or "")
    if status not in STATUSES:
        raise ValueError(f"unsupported task status: {status or '<missing>'}")
    if not isinstance(state.get("task"), str) or not str(state["task"]).strip():
        raise ValueError("task state requires task")
    if not isinstance(state.get("intent"), str) or not str(state["intent"]).strip():
        raise ValueError("task state requires intent")
    risk = state.get("risk")
    if not isinstance(risk, dict) or str(risk.get("level") or "") not in RISK_LEVELS:
        raise ValueError("task state has invalid risk level")
    if not isinstance(risk.get("reasons"), list):
        raise ValueError("task state risk reasons must be a list")
    confirmed_by = risk.get("confirmed_by")
    if confirmed_by is not None and (not isinstance(confirmed_by, str) or not confirmed_by.strip()):
        raise ValueError("task state risk confirmed_by must be null or a non-empty string")
    expected_types = {
        "baseline": dict,
        "acceptance": list,
        "scope": dict,
        "diagnosis": dict,
        "verification": list,
        "understanding": dict,
        "knowledge_candidates": list,
        "timestamps": dict,
        "history": list,
    }
    for field, expected_type in expected_types.items():
        if not isinstance(state.get(field), expected_type):
            raise ValueError(f"task state field {field} must be {expected_type.__name__}")


def save_task_state(repo_root: Path, state: dict[str, Any]) -> None:
    _validate_state(state)
    path = _state_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(state, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        temporary = Path(temp_name)
        if temporary.exists():
            temporary.unlink()


def load_task_state(repo_root: Path) -> dict[str, Any]:
    path = _state_path(repo_root)
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid task state JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError("task state must be an object")
    _validate_state(payload)
    return payload


def create_task_state(repo_root: Path, task: str, intent: str) -> dict[str, Any]:
    selected_task = task.strip()
    selected_intent = intent.strip()
    if not selected_task:
        raise ValueError("task is required")
    if not selected_intent:
        raise ValueError("intent is required")
    now = _now()
    state: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "task_id": _task_id(selected_task, now),
        "task": selected_task,
        "intent": selected_intent,
        "status": str(REGISTRY["default_status"]),
        "risk": {"level": str(REGISTRY["default_risk"]), "reasons": [], "confirmed_by": None},
        "baseline": {},
        "acceptance": [],
        "scope": {"allowed": [], "changed": [], "drift": []},
        "diagnosis": {"reproduction": None, "root_cause": None, "minimal_fix": None},
        "verification": [],
        "understanding": {},
        "knowledge_candidates": [],
        "timestamps": {"created_at": now, "updated_at": now, "status_changed_at": now},
        "history": [
            {
                "from": "detected",
                "to": str(REGISTRY["default_status"]),
                "reason": "task detected",
                "at": now,
            }
        ],
    }
    save_task_state(repo_root, state)
    return state


def classify_risk(
    task: str,
    *,
    intent: str = "",
    paths: list[str] | tuple[str, ...] | None = None,
    uncertain: bool = False,
) -> dict[str, Any]:
    evidence = " ".join(
        item.strip().lower()
        for item in [task, intent, *(paths or [])]
        if isinstance(item, str) and item.strip()
    )
    matched_by_level: dict[str, list[str]] = {level: [] for level in RISK_ORDER}
    for rule in RISK_RULES:
        keywords = [str(item).lower() for item in rule.get("keywords", [])]
        groups = [
            [str(item).lower() for item in group]
            for group in rule.get("all_keyword_groups", [])
            if isinstance(group, list)
        ]
        keyword_match = bool(keywords) and any(keyword in evidence for keyword in keywords)
        group_match = bool(groups) and all(any(keyword in evidence for keyword in group) for group in groups)
        if keyword_match or group_match:
            matched_by_level[str(rule["level"])].append(str(rule["reason"]))

    selected_level = str(REGISTRY["default_risk"])
    reasons = ["normal local engineering change"]
    for level in reversed(RISK_ORDER):
        if matched_by_level[level]:
            selected_level = level
            reasons = matched_by_level[level]
            break

    if uncertain:
        current_index = RISK_ORDER.index(selected_level)
        selected_level = RISK_ORDER[min(current_index + 1, len(RISK_ORDER) - 1)]
        reasons = [*reasons, "uncertainty requires conservative one-level promotion"]

    return {"level": selected_level, "reasons": reasons, "source": "deterministic-rule"}


def set_task_risk(repo_root: Path, classification: dict[str, Any]) -> dict[str, Any]:
    level = str(classification.get("level") or "")
    reasons = classification.get("reasons")
    source = str(classification.get("source") or "")
    if level not in RISK_LEVELS or not isinstance(reasons, list) or not reasons:
        raise ValueError("valid risk classification is required")
    if source != "deterministic-rule":
        raise ValueError("risk classification source must be deterministic-rule")
    state = load_task_state(repo_root)
    if not state:
        raise ValueError("task state does not exist")
    updated = dict(state)
    updated["risk"] = {
        "level": level,
        "reasons": [str(reason) for reason in reasons],
        "source": source,
        "confirmed_by": None,
        "confirmed_at": None,
    }
    updated["timestamps"] = {**dict(state["timestamps"]), "updated_at": _now()}
    save_task_state(repo_root, updated)
    return updated


def confirm_task_risk(repo_root: Path, confirmed_by: str) -> dict[str, Any]:
    selected_confirmer = confirmed_by.strip()
    if not selected_confirmer:
        raise ValueError("responsibility confirmation requires confirmed_by")
    state = load_task_state(repo_root)
    if not state:
        raise ValueError("task state does not exist")
    now = _now()
    updated = dict(state)
    updated["risk"] = {
        **dict(state["risk"]),
        "confirmed_by": selected_confirmer,
        "confirmed_at": now,
    }
    updated["timestamps"] = {**dict(state["timestamps"]), "updated_at": now}
    save_task_state(repo_root, updated)
    return updated


def record_task_contract(
    repo_root: Path,
    *,
    reproduction: str | None = None,
    reproduction_unavailable_evidence: str | None = None,
    root_cause: str | None = None,
    minimal_fix: str | None = None,
    acceptance: list[str] | None = None,
) -> dict[str, Any]:
    state = load_task_state(repo_root)
    if not state:
        raise ValueError("task state does not exist")
    if reproduction is not None and reproduction_unavailable_evidence is not None:
        raise ValueError("record reproduction or unavailable evidence, not both")

    diagnosis = dict(state["diagnosis"])
    if reproduction is not None:
        diagnosis["reproduction"] = {"status": "reproduced", "evidence": reproduction.strip()}
    elif reproduction_unavailable_evidence is not None:
        diagnosis["reproduction"] = {
            "status": "not_reproduced",
            "evidence": reproduction_unavailable_evidence.strip(),
        }
    if root_cause is not None:
        diagnosis["root_cause"] = root_cause.strip()
    if minimal_fix is not None:
        diagnosis["minimal_fix"] = minimal_fix.strip()
    recheck = diagnosis.get("recheck_required")
    if (
        isinstance(recheck, dict)
        and root_cause is not None
        and root_cause.strip()
        and minimal_fix is not None
        and minimal_fix.strip()
    ):
        acceptance_id = str(recheck.get("acceptance_id") or "")
        patch_loop = dict(diagnosis.get("patch_loop") or {})
        streaks = dict(patch_loop.get("streaks") or {})
        if acceptance_id in streaks:
            streaks[acceptance_id] = {"count": 0, "last_implementation_id": None}
        diagnosis["patch_loop"] = {**patch_loop, "streaks": streaks}
        diagnosis.pop("recheck_required", None)
    if acceptance is not None:
        if not isinstance(acceptance, list):
            raise ValueError("acceptance must be a list")
        selected_acceptance = [str(item).strip() for item in acceptance if str(item).strip()]
    else:
        selected_acceptance = list(state["acceptance"])

    updated = dict(state)
    updated["diagnosis"] = diagnosis
    updated["acceptance"] = selected_acceptance
    updated["timestamps"] = {**dict(state["timestamps"]), "updated_at": _now()}
    save_task_state(repo_root, updated)
    return updated


def _bug_contract_missing(state: dict[str, Any]) -> list[str]:
    intent = re.sub(r"[-\s]+", "_", str(state.get("intent") or "").strip().lower())
    if intent not in {"bug", "bug_fix", "bugfix"}:
        return []
    diagnosis = dict(state["diagnosis"])
    reproduction = diagnosis.get("reproduction")
    valid_reproduction = (
        isinstance(reproduction, dict)
        and reproduction.get("status") in {"reproduced", "not_reproduced"}
        and isinstance(reproduction.get("evidence"), str)
        and bool(reproduction["evidence"].strip())
    )
    missing: list[str] = []
    if not valid_reproduction:
        missing.append("reproduction")
    if not isinstance(diagnosis.get("root_cause"), str) or not diagnosis["root_cause"].strip():
        missing.append("root_cause")
    if not isinstance(diagnosis.get("minimal_fix"), str) or not diagnosis["minimal_fix"].strip():
        missing.append("minimal_fix")
    acceptance = state.get("acceptance")
    if not isinstance(acceptance, list) or not any(isinstance(item, str) and item.strip() for item in acceptance):
        missing.append("acceptance")
    return missing


def _normalize_scope_path(value: str, *, allow_directory: bool = False) -> str:
    selected = value.strip().replace("\\", "/")
    directory = allow_directory and selected.endswith("/")
    selected = selected.rstrip("/")
    if not selected or selected.startswith("/") or re.match(r"^[a-zA-Z]:", selected):
        raise ValueError("scope paths must be relative to the project")
    parts = selected.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError("scope paths must not escape the project")
    return f"{selected}/" if directory else selected


def set_task_scope(repo_root: Path, allowed: list[str]) -> dict[str, Any]:
    if not isinstance(allowed, list):
        raise ValueError("allowed scope must be a list")
    state = load_task_state(repo_root)
    if not state:
        raise ValueError("task state does not exist")
    selected_allowed = sorted({_normalize_scope_path(str(path), allow_directory=True) for path in allowed})
    updated = dict(state)
    updated["scope"] = {"allowed": selected_allowed, "changed": [], "drift": []}
    updated["timestamps"] = {**dict(state["timestamps"]), "updated_at": _now()}
    save_task_state(repo_root, updated)
    return updated


def _path_is_allowed(path: str, allowed: list[str]) -> bool:
    return any(path == item or (item.endswith("/") and path.startswith(item)) for item in allowed)


def _scope_drift_reasons(path: str, allowed: list[str]) -> list[str]:
    parts = path.lower().split("/")
    name = parts[-1]
    reasons = ["unplanned_path"]
    allowed_roots = {item.rstrip("/").split("/", 1)[0].lower() for item in allowed}
    if len(parts) > 1 and parts[0] not in allowed_roots:
        reasons.append("new_directory")
    if any(part in {"architecture", "application", "domain", "infrastructure"} for part in parts[:-1]):
        reasons.append("architecture_layer")
    dependency_files = {
        "requirements.txt",
        "pyproject.toml",
        "poetry.lock",
        "uv.lock",
        "package.json",
        "package-lock.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "go.mod",
        "go.sum",
        "cargo.toml",
        "cargo.lock",
    }
    if name in dependency_files:
        reasons.append("dependency_change")
    if any(part in {"migration", "migrations", "alembic"} for part in parts):
        reasons.append("database_migration")
    deployment_parts = {"deploy", "deployment", "k8s", "kubernetes", "terraform", "helm", "workflows"}
    if any(part in deployment_parts for part in parts) or name.startswith(("dockerfile", "docker-compose")):
        reasons.append("deployment_configuration")
    return reasons


def _block_state(state: dict[str, Any], reason: str) -> dict[str, Any]:
    if state["status"] == "blocked":
        return state
    if "blocked" not in TRANSITIONS.get(str(state["status"]), frozenset()):
        raise ValueError(f"cannot block task from status {state['status']}")
    now = _now()
    source = str(state["status"])
    updated = dict(state)
    updated["status"] = "blocked"
    updated["timestamps"] = {
        **dict(state["timestamps"]),
        "updated_at": now,
        "status_changed_at": now,
    }
    updated["history"] = [
        *list(state["history"]),
        {"from": source, "to": "blocked", "reason": reason, "at": now},
    ]
    return updated


def evaluate_scope(repo_root: Path, changed_paths: list[str] | None = None) -> dict[str, Any]:
    state = load_task_state(repo_root)
    if not state:
        raise ValueError("task state does not exist")
    if changed_paths is None:
        comparison = compare_with_baseline(repo_root, dict(state["baseline"]))
        if comparison["stale"]:
            raise ValueError("cannot evaluate scope from a stale Git baseline")
        selected_changed = [_normalize_scope_path(path) for path in comparison["task_changes"]]
    else:
        if not isinstance(changed_paths, list):
            raise ValueError("changed_paths must be a list")
        selected_changed = [_normalize_scope_path(str(path)) for path in changed_paths]
    selected_changed = sorted(set(selected_changed))
    allowed = [str(path) for path in state["scope"].get("allowed", [])]
    drift = [
        {"path": path, "reasons": _scope_drift_reasons(path, allowed)}
        for path in selected_changed
        if not _path_is_allowed(path, allowed)
    ]

    effective_level = str(state["risk"]["level"])
    if any(
        reason in {"database_migration", "deployment_configuration"}
        for item in drift
        for reason in item["reasons"]
    ):
        effective_level = RISK_ORDER[max(RISK_ORDER.index(effective_level), RISK_ORDER.index("P1"))]
    explicit_risk = classify_risk("scope drift", paths=[item["path"] for item in drift])
    if explicit_risk["reasons"] != ["normal local engineering change"]:
        effective_level = RISK_ORDER[
            max(RISK_ORDER.index(effective_level), RISK_ORDER.index(str(explicit_risk["level"])))
        ]

    action = "continue"
    blocking = False
    if drift and effective_level == "P3":
        action = "warn"
    elif drift and effective_level == "P2":
        action = "replan"
        blocking = True
    elif drift:
        action = "reconfirm"
        blocking = True

    updated = dict(state)
    updated["scope"] = {"allowed": allowed, "changed": selected_changed, "drift": drift}
    if action == "reconfirm":
        updated["risk"] = {
            **dict(state["risk"]),
            "level": effective_level,
            "reasons": [*list(state["risk"].get("reasons", [])), "scope drift requires reconfirmation"],
            "source": "deterministic-rule",
            "confirmed_by": None,
            "confirmed_at": None,
        }
    if blocking:
        updated = _block_state(updated, f"scope drift requires {action}")
    else:
        updated["timestamps"] = {**dict(state["timestamps"]), "updated_at": _now()}
    save_task_state(repo_root, updated)
    return {
        "changed": selected_changed,
        "drift": drift,
        "effective_level": effective_level,
        "action": action,
        "blocking": blocking,
    }


def record_acceptance_attempt(
    repo_root: Path,
    acceptance_id: str,
    implementation_id: str,
    *,
    passed: bool,
) -> dict[str, Any]:
    selected_acceptance = acceptance_id.strip()
    selected_implementation = implementation_id.strip()
    if not selected_acceptance or not selected_implementation:
        raise ValueError("acceptance_id and implementation_id are required")
    if not isinstance(passed, bool):
        raise ValueError("passed must be a boolean")
    state = load_task_state(repo_root)
    if not state:
        raise ValueError("task state does not exist")
    if state["diagnosis"].get("recheck_required"):
        raise ValueError("root-cause recheck required before another implementation")
    if state["status"] not in {"implementing", "verifying"}:
        raise ValueError("acceptance attempts require an implementation in progress")

    diagnosis = dict(state["diagnosis"])
    patch_loop = dict(diagnosis.get("patch_loop") or {})
    streaks = dict(patch_loop.get("streaks") or {})
    streak = dict(streaks.get(selected_acceptance) or {"count": 0, "last_implementation_id": None})
    counted = False
    if passed:
        streak = {"count": 0, "last_implementation_id": None}
    elif streak.get("last_implementation_id") != selected_implementation:
        streak = {"count": int(streak.get("count") or 0) + 1, "last_implementation_id": selected_implementation}
        counted = True
    streaks[selected_acceptance] = streak
    events = [
        *list(patch_loop.get("events") or []),
        {
            "acceptance_id": selected_acceptance,
            "implementation_id": selected_implementation,
            "passed": passed,
            "counted": counted,
            "recorded_at": _now(),
        },
    ]
    diagnosis["patch_loop"] = {"streaks": streaks, "events": events}

    recheck_required = not passed and int(streak["count"]) >= 3
    if recheck_required:
        diagnosis["recheck_required"] = {
            "acceptance_id": selected_acceptance,
            "reason": "three distinct implementations failed the same acceptance condition",
        }
    updated = dict(state)
    updated["diagnosis"] = diagnosis
    if recheck_required:
        updated = _block_state(updated, "patch loop requires root-cause recheck")
    else:
        updated["timestamps"] = {**dict(state["timestamps"]), "updated_at": _now()}
    save_task_state(repo_root, updated)
    return {
        "acceptance_id": selected_acceptance,
        "implementation_id": selected_implementation,
        "failure_count": int(streak["count"]),
        "counted": counted,
        "status": str(updated["status"]),
        "recheck_required": recheck_required,
    }


def transition_task(repo_root: Path, target: str, *, reason: str = "") -> dict[str, Any]:
    state = load_task_state(repo_root)
    if not state:
        raise ValueError("task state does not exist")
    source = str(state["status"])
    selected_target = target.strip()
    if selected_target not in STATUSES:
        raise ValueError(f"unsupported task status: {selected_target or '<missing>'}")
    if selected_target not in TRANSITIONS.get(source, frozenset()):
        raise ValueError(f"invalid task transition: {source} -> {selected_target}")
    if selected_target in {"planned", "awaiting_approval", "implementing"}:
        missing_contract = _bug_contract_missing(state)
        if missing_contract:
            raise ValueError(f"bug implementation contract incomplete: {', '.join(missing_contract)}")
    risk = dict(state["risk"])
    if selected_target == "implementing" and risk["level"] in {"P1", "P0"} and not risk.get("confirmed_by"):
        raise ValueError(f"{risk['level']} task requires responsibility confirmation before implementing")
    now = _now()
    updated = dict(state)
    updated["status"] = selected_target
    updated["timestamps"] = {
        **dict(state["timestamps"]),
        "updated_at": now,
        "status_changed_at": now,
    }
    updated["history"] = [
        *list(state["history"]),
        {"from": source, "to": selected_target, "reason": reason.strip(), "at": now},
    ]
    save_task_state(repo_root, updated)
    return updated


def _git_output(repo_root: Path, args: list[str]) -> tuple[int, str]:
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
        return 127, ""
    return completed.returncode, completed.stdout.rstrip("\r\n")


def _git_paths(repo_root: Path, args: list[str]) -> list[str]:
    output = _git_output(repo_root, args)[1]
    return sorted({line.strip().replace("\\", "/") for line in output.splitlines() if line.strip()})


def _path_hash(repo_root: Path, relative_path: str) -> str:
    path = repo_root / relative_path
    if not path.is_file():
        return "<missing>"
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def capture_git_baseline(repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    repository_code, repository_flag = _git_output(root, ["rev-parse", "--is-inside-work-tree"])
    is_repository = repository_code == 0 and repository_flag == "true"
    head_code, head_output = _git_output(root, ["rev-parse", "HEAD"]) if is_repository else (1, "")
    head = head_output if head_code == 0 else ""
    if is_repository and head:
        tracked = _git_paths(root, ["diff", "--name-only", "HEAD", "--"])
    elif is_repository:
        tracked = sorted(
            set(_git_paths(root, ["diff", "--name-only", "--"]))
            | set(_git_paths(root, ["diff", "--cached", "--name-only", "--"]))
        )
    else:
        tracked = []
    untracked = _git_paths(root, ["ls-files", "--others", "--exclude-standard"]) if is_repository else []
    dirty_paths = sorted(set(tracked) | set(untracked))
    return {
        "is_git_repository": is_repository,
        "branch": _git_output(root, ["branch", "--show-current"])[1] if is_repository else "",
        "head": head,
        "tracked_modified": tracked,
        "untracked": untracked,
        "path_hashes": {path: _path_hash(root, path) for path in dirty_paths},
        "captured_at": _now(),
    }


def compare_with_baseline(repo_root: Path, baseline: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(baseline, dict) or "captured_at" not in baseline:
        raise ValueError("valid Git baseline is required")
    current = capture_git_baseline(repo_root)
    previous_paths = sorted(
        set(str(item) for item in baseline.get("tracked_modified", []))
        | set(str(item) for item in baseline.get("untracked", []))
    )
    current_paths = sorted(set(current["tracked_modified"]) | set(current["untracked"]))
    previous_hashes = baseline.get("path_hashes") if isinstance(baseline.get("path_hashes"), dict) else {}
    current_hashes = current["path_hashes"]
    task_added = sorted(set(current_paths) - set(previous_paths))
    task_touched_preexisting = sorted(
        path
        for path in set(current_paths) & set(previous_paths)
        if str(previous_hashes.get(path, "")) != str(current_hashes.get(path, ""))
    )
    stale_reasons: list[str] = []
    if bool(baseline.get("is_git_repository")) != bool(current["is_git_repository"]):
        stale_reasons.append("repository_state_changed")
    if str(baseline.get("branch") or "") != str(current["branch"] or ""):
        stale_reasons.append("branch_changed")
    if str(baseline.get("head") or "") != str(current["head"] or ""):
        stale_reasons.append("head_changed")
    return {
        "stale": bool(stale_reasons),
        "stale_reasons": stale_reasons,
        "baseline": baseline,
        "current": current,
        "preexisting_changes": previous_paths,
        "preexisting_remaining": sorted(set(current_paths) & set(previous_paths)),
        "preexisting_resolved": sorted(set(previous_paths) - set(current_paths)),
        "task_added": task_added,
        "task_touched_preexisting": task_touched_preexisting,
        "task_changes": sorted(set(task_added) | set(task_touched_preexisting)),
    }


def resume_summary(repo_root: Path) -> dict[str, Any]:
    state = load_task_state(repo_root)
    if not state:
        return {"status": "none", "task_id": "", "task": "", "comparison": {}}
    baseline = state.get("baseline")
    if not isinstance(baseline, dict) or not baseline:
        return {
            "status": str(state["status"]),
            "task_id": str(state["task_id"]),
            "task": str(state["task"]),
            "comparison": {"stale": True, "stale_reasons": ["baseline_missing"]},
        }
    comparison = compare_with_baseline(repo_root, baseline)
    status = str(state["status"])
    if comparison["stale"] and status not in {"stale", "closed", "abandoned"}:
        state = transition_task(repo_root, "stale", reason=", ".join(comparison["stale_reasons"]))
        status = str(state["status"])
    return {
        "status": status,
        "task_id": str(state["task_id"]),
        "task": str(state["task"]),
        "comparison": comparison,
    }
