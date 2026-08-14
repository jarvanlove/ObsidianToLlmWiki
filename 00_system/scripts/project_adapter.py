from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

from wiki_lib import SCRIPT_DIR


DEFAULT_TEMPLATE_ROOT = SCRIPT_DIR.parent.parent / "docs" / "templates" / "project-adapters"
ADAPTER_SCHEMA_PATH = SCRIPT_DIR.parent / "registry" / "project_adapter_schema.json"
STATE_REL_PATH = Path(".obsidiantowiki/adapter-state.json")
CANDIDATE_REL_ROOT = Path(".obsidiantowiki/upgrade-candidates")


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def current_adapter_version() -> int:
    try:
        payload = json.loads(ADAPTER_SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot read project adapter schema: {exc}") from exc
    version = payload.get("current_adapter_version") if isinstance(payload, dict) else None
    if not isinstance(version, int) or version < 1:
        raise RuntimeError("project adapter schema has an invalid current_adapter_version")
    return version


def adapter_state_schema_version() -> int:
    try:
        payload = json.loads(ADAPTER_SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot read project adapter schema: {exc}") from exc
    version = payload.get("state_schema_version") if isinstance(payload, dict) else None
    if not isinstance(version, int) or version < 1:
        raise RuntimeError("project adapter schema has an invalid state_schema_version")
    return version


def template_snapshot(template_root: Path) -> dict[str, dict[str, object]]:
    snapshot: dict[str, dict[str, object]] = {}
    for path in sorted(template_root.rglob("*"), key=lambda item: item.as_posix().lower()):
        if path.is_file():
            rel_path = path.relative_to(template_root).as_posix()
            snapshot[rel_path] = {"path": path, "hash": file_sha256(path)}
    if not snapshot:
        raise RuntimeError(f"adapter template root has no files: {template_root}")
    return snapshot


def load_state(repo_root: Path) -> dict[str, object]:
    state_path = repo_root / STATE_REL_PATH
    supported_schema = adapter_state_schema_version()
    if not state_path.exists():
        return {
            "schema_version": supported_schema,
            "adapter_version": 0,
            "target_adapter_version": 0,
            "managed_files": {},
            "conflicts": [],
        }
    try:
        payload = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot read adapter state {state_path}: {exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("schema_version"), int):
        raise RuntimeError(f"adapter state requires schema_version={supported_schema}: {state_path}")
    actual_schema = int(payload["schema_version"])
    if actual_schema > supported_schema:
        raise RuntimeError(
            f"adapter state schema {actual_schema} is newer than this runtime supports ({supported_schema}): {state_path}"
        )
    if actual_schema != supported_schema:
        raise RuntimeError(f"adapter state requires schema_version={supported_schema}: {state_path}")
    if not isinstance(payload.get("managed_files"), dict):
        raise RuntimeError(f"adapter state managed_files must be an object: {state_path}")
    return payload


def inspect_adapter(
    repo_root: Path,
    *,
    template_root: Path = DEFAULT_TEMPLATE_ROOT,
    target_version: int | None = None,
) -> dict[str, object]:
    repo_root = repo_root.expanduser().resolve()
    version = target_version or current_adapter_version()
    state = load_state(repo_root)
    installed_version = int(state.get("adapter_version") or 0)
    if installed_version > version:
        raise RuntimeError(f"project adapter version {installed_version} is newer than runtime target {version}")
    previous_files = state.get("managed_files") if isinstance(state.get("managed_files"), dict) else {}
    desired = template_snapshot(template_root)
    actions: list[dict[str, str]] = []
    conflicts: list[str] = []
    for rel_path, item in desired.items():
        destination = repo_root / Path(rel_path)
        desired_hash = str(item["hash"])
        previous = previous_files.get(rel_path)
        previous_hash = str(previous.get("installed_hash") or "") if isinstance(previous, dict) else ""
        if not destination.exists():
            action = "create"
        else:
            current_hash = file_sha256(destination)
            if current_hash == desired_hash:
                action = "unchanged"
            elif previous_hash and current_hash == previous_hash:
                action = "update"
            else:
                action = "conflict"
                conflicts.append(rel_path)
        actions.append({"path": rel_path, "action": action})

    obsolete = sorted(set(str(item) for item in previous_files) - set(desired))
    if conflicts:
        status = "conflicts"
    elif installed_version == version and all(item["action"] == "unchanged" for item in actions):
        status = "current"
    elif installed_version == 0 and all(item["action"] == "create" for item in actions):
        status = "not_installed"
    else:
        status = "upgrade_available"
    return {
        "schema_version": adapter_state_schema_version(),
        "repo_root": str(repo_root),
        "state_path": STATE_REL_PATH.as_posix(),
        "adapter_version": installed_version,
        "target_adapter_version": version,
        "status": status,
        "actions": actions,
        "conflicts": conflicts,
        "obsolete_managed_files": obsolete,
    }


def write_json_atomic(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temp_name, path)
    finally:
        temp_path = Path(temp_name)
        if temp_path.exists():
            temp_path.unlink()


def apply_adapter_upgrade(
    repo_root: Path,
    *,
    template_root: Path = DEFAULT_TEMPLATE_ROOT,
    target_version: int | None = None,
) -> dict[str, object]:
    repo_root = repo_root.expanduser().resolve()
    version = target_version or current_adapter_version()
    report = inspect_adapter(repo_root, template_root=template_root, target_version=version)
    previous_state = load_state(repo_root)
    previous_files = previous_state.get("managed_files") if isinstance(previous_state.get("managed_files"), dict) else {}
    desired = template_snapshot(template_root)

    for action in report["actions"]:
        rel_path = str(action["path"])
        source = Path(str(desired[rel_path]["path"]))
        destination = repo_root / Path(rel_path)
        if action["action"] in {"create", "update"}:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source.read_bytes())
        elif action["action"] == "conflict":
            candidate = repo_root / CANDIDATE_REL_ROOT / f"v{version}" / Path(f"{rel_path}.new")
            candidate.parent.mkdir(parents=True, exist_ok=True)
            candidate.write_bytes(source.read_bytes())

    managed_files: dict[str, dict[str, str]] = {}
    for rel_path, item in desired.items():
        destination = repo_root / Path(rel_path)
        desired_hash = str(item["hash"])
        if destination.exists() and file_sha256(destination) == desired_hash:
            managed_files[rel_path] = {"installed_hash": desired_hash}
        else:
            previous = previous_files.get(rel_path)
            if isinstance(previous, dict) and str(previous.get("installed_hash") or ""):
                managed_files[rel_path] = {"installed_hash": str(previous["installed_hash"])}

    conflicts = [str(item) for item in report["conflicts"]]
    installed_version = int(previous_state.get("adapter_version") or 0) if conflicts else version
    state = {
        "schema_version": adapter_state_schema_version(),
        "adapter_version": installed_version,
        "target_adapter_version": version,
        "managed_files": managed_files,
        "conflicts": conflicts,
    }
    write_json_atomic(repo_root / STATE_REL_PATH, state)
    result = inspect_adapter(repo_root, template_root=template_root, target_version=version)
    result["applied"] = [item for item in report["actions"] if item["action"] in {"create", "update"}]
    result["staged_conflicts"] = conflicts
    if conflicts:
        result["status"] = "conflicts"
        result["adapter_version"] = installed_version
    return result


def render_text(payload: dict[str, object]) -> str:
    lines = [
        "Project Adapter Compatibility",
        f"repo_root={payload['repo_root']}",
        f"status={payload['status']}",
        f"adapter_version={payload['adapter_version']} target={payload['target_adapter_version']}",
    ]
    for item in payload["actions"]:
        lines.append(f"{item['action']}: {item['path']}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect or safely upgrade ObsidianToWiki project adapters.")
    parser.add_argument("command", choices=["report", "apply"])
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()
    repo_root = Path(args.repo_root)
    payload = inspect_adapter(repo_root) if args.command == "report" else apply_adapter_upgrade(repo_root)
    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.format == "json" else render_text(payload))


if __name__ == "__main__":
    main()
