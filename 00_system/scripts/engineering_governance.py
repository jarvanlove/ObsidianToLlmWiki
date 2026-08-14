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
