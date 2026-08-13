from __future__ import annotations

import hashlib
import json
import os
import re
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
