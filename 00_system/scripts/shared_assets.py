from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

from wiki_lib import SCRIPT_DIR, VAULT_ROOT


DEFAULT_SOURCE_ROOT = SCRIPT_DIR.parent.parent
DEFAULT_MANIFEST_PATH = SCRIPT_DIR.parent / "registry" / "shared_assets.json"
STATE_REL_PATH = Path("00_system/registry/vault_state.json")
CANDIDATE_REL_ROOT = Path("40_outputs/upgrade-candidates/shared")
RESOLUTION_VALUES = {"merged", "keep-local"}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest(path: Path = DEFAULT_MANIFEST_PATH) -> tuple[int, list[dict[str, object]]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot read shared asset manifest: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise RuntimeError("shared asset manifest requires schema_version=1")
    release = payload.get("release_version")
    assets = payload.get("assets")
    if not isinstance(release, int) or release < 1 or not isinstance(assets, list):
        raise RuntimeError("shared asset manifest has an invalid release or assets list")
    normalized: list[dict[str, object]] = []
    for item in assets:
        if not isinstance(item, dict):
            raise RuntimeError("shared asset manifest contains a non-object asset")
        rel_path = str(item.get("path") or "").strip().replace("\\", "/")
        version = item.get("version")
        if not rel_path or Path(rel_path).is_absolute() or ".." in Path(rel_path).parts:
            raise RuntimeError(f"shared asset manifest contains an invalid path: {rel_path}")
        if not isinstance(version, int) or version < 1:
            raise RuntimeError(f"shared asset manifest contains an invalid version for {rel_path}")
        normalized.append({"path": rel_path, "version": version})
    return release, normalized


def load_vault_state(vault_root: Path) -> dict[str, object]:
    state_path = vault_root / STATE_REL_PATH
    if not state_path.exists():
        raise RuntimeError("vault_state.json is missing; run vault_compat.py migrate --apply first")
    try:
        payload = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot read vault state: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise RuntimeError("vault_state.json requires schema_version=1")
    shared_assets = payload.get("shared_assets")
    if shared_assets is None:
        payload["shared_assets"] = {}
    elif not isinstance(shared_assets, dict):
        raise RuntimeError("vault_state.json shared_assets must be an object")
    return payload


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


def inspect_shared_assets(
    *,
    vault_root: Path,
    source_root: Path,
    release_version: int,
    assets: list[dict[str, object]],
) -> dict[str, object]:
    vault_root = vault_root.expanduser().resolve()
    source_root = source_root.expanduser().resolve()
    state = load_vault_state(vault_root)
    baselines = state.get("shared_assets") if isinstance(state.get("shared_assets"), dict) else {}
    results: list[dict[str, object]] = []
    for asset in assets:
        rel_path = str(asset["path"])
        source = source_root / Path(rel_path)
        destination = vault_root / Path(rel_path)
        source_hash = file_sha256(source) if source.exists() else ""
        private_hash = file_sha256(destination) if destination.exists() else ""
        previous = baselines.get(rel_path) if isinstance(baselines.get(rel_path), dict) else {}
        previous_source = str(previous.get("source_hash") or "")
        previous_private = str(previous.get("private_hash") or "")
        resolution = str(previous.get("resolution") or "")
        if not source.exists():
            status = "source_missing"
        elif not destination.exists():
            status = "missing"
        elif source_hash == private_hash:
            status = "current"
        elif (
            resolution in RESOLUTION_VALUES
            and source_hash == previous_source
            and private_hash == previous_private
        ):
            status = "resolved_local"
        elif previous_private and private_hash == previous_private and previous_private == previous_source:
            status = "safe_update"
        else:
            status = "conflict"
        results.append(
            {
                "path": rel_path,
                "asset_version": int(asset["version"]),
                "status": status,
                "source_hash": source_hash,
                "private_hash": private_hash,
                "resolution": resolution if status == "resolved_local" else "",
            }
        )
    return {
        "schema_version": 1,
        "vault_root": str(vault_root),
        "source_root": str(source_root),
        "release_version": release_version,
        "assets": results,
    }


def apply_shared_asset_action(
    action: str,
    *,
    vault_root: Path,
    source_root: Path,
    release_version: int,
    assets: list[dict[str, object]],
) -> dict[str, object]:
    if action not in {"stage", "apply-safe"}:
        raise ValueError(f"unsupported shared asset action: {action}")
    vault_root = vault_root.expanduser().resolve()
    source_root = source_root.expanduser().resolve()
    before = inspect_shared_assets(
        vault_root=vault_root,
        source_root=source_root,
        release_version=release_version,
        assets=assets,
    )
    state = load_vault_state(vault_root)
    baselines = state.get("shared_assets") if isinstance(state.get("shared_assets"), dict) else {}
    updated = 0
    staged = 0
    conflicts = 0
    resolved_local = 0
    for item in before["assets"]:
        rel_path = str(item["path"])
        status = str(item["status"])
        source = source_root / Path(rel_path)
        destination = vault_root / Path(rel_path)
        if status == "current":
            baselines[rel_path] = {
                "asset_version": item["asset_version"],
                "source_hash": item["source_hash"],
                "private_hash": item["private_hash"],
            }
            continue
        if status == "resolved_local":
            resolved_local += 1
            continue
        if status == "source_missing":
            conflicts += 1
            continue
        if action == "apply-safe" and status in {"safe_update", "missing"}:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source.read_bytes())
            digest = file_sha256(destination)
            baselines[rel_path] = {
                "asset_version": item["asset_version"],
                "source_hash": digest,
                "private_hash": digest,
            }
            updated += 1
            continue
        candidate = vault_root / CANDIDATE_REL_ROOT / f"v{release_version}" / Path(f"{rel_path}.new")
        candidate.parent.mkdir(parents=True, exist_ok=True)
        candidate.write_bytes(source.read_bytes())
        staged += 1
        if status == "conflict":
            conflicts += 1

    state["shared_assets"] = baselines
    write_json_atomic(vault_root / STATE_REL_PATH, state)
    report = inspect_shared_assets(
        vault_root=vault_root,
        source_root=source_root,
        release_version=release_version,
        assets=assets,
    )
    current = sum(1 for item in report["assets"] if item["status"] == "current")
    report["action"] = action
    report["summary"] = {
        "total": len(report["assets"]),
        "current": current,
        "resolved_local": resolved_local,
        "updated": updated,
        "staged": staged,
        "conflicts": conflicts,
    }
    report_path = vault_root / CANDIDATE_REL_ROOT / f"v{release_version}" / "report.json"
    write_json_atomic(report_path, report)
    report["report_path"] = report_path.relative_to(vault_root).as_posix()
    return report


def resolve_shared_asset(
    *,
    vault_root: Path,
    source_root: Path,
    release_version: int,
    assets: list[dict[str, object]],
    rel_path: str,
    resolution: str,
) -> dict[str, object]:
    if resolution not in RESOLUTION_VALUES:
        raise ValueError(f"unsupported shared asset resolution: {resolution}")
    rel_path = rel_path.strip().replace("\\", "/")
    asset = next((item for item in assets if item["path"] == rel_path), None)
    if asset is None:
        raise ValueError(f"shared asset is not managed: {rel_path}")

    vault_root = vault_root.expanduser().resolve()
    source_root = source_root.expanduser().resolve()
    source = source_root / Path(rel_path)
    destination = vault_root / Path(rel_path)
    candidate = vault_root / CANDIDATE_REL_ROOT / f"v{release_version}" / Path(f"{rel_path}.new")
    if not source.exists() or not destination.exists() or not candidate.exists():
        raise ValueError(f"shared asset resolution requires source, local file, and current candidate: {rel_path}")
    if file_sha256(candidate) != file_sha256(source):
        raise ValueError(f"shared asset candidate does not match the current source: {rel_path}")

    state = load_vault_state(vault_root)
    baselines = state.get("shared_assets") if isinstance(state.get("shared_assets"), dict) else {}
    baselines[rel_path] = {
        "asset_version": int(asset["version"]),
        "source_hash": file_sha256(source),
        "private_hash": file_sha256(destination),
        "resolution": resolution,
        "resolved_at": datetime.now().replace(microsecond=0).isoformat(),
    }
    state["shared_assets"] = baselines
    write_json_atomic(vault_root / STATE_REL_PATH, state)

    removed_candidates: list[str] = []
    for version_dir in (vault_root / CANDIDATE_REL_ROOT).glob("v*"):
        stale = version_dir / Path(f"{rel_path}.new")
        if stale.exists():
            stale.unlink()
            removed_candidates.append(stale.relative_to(vault_root).as_posix())
    return {
        "schema_version": 1,
        "release_version": release_version,
        "path": rel_path,
        "status": "resolved_local",
        "resolution": resolution,
        "removed_candidates": removed_candidates,
    }


def summarize(report: dict[str, object]) -> dict[str, int]:
    statuses = [str(item["status"]) for item in report["assets"]]
    return {
        status: statuses.count(status)
        for status in ("current", "resolved_local", "safe_update", "missing", "conflict", "source_missing")
    }


def render_text(payload: dict[str, object]) -> str:
    if payload.get("status") == "resolved_local" and "assets" not in payload:
        return (
            "Shared Asset Resolution\n"
            f"release_version={payload['release_version']}\n"
            f"{payload['resolution']}: {payload['path']}"
        )
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else summarize(payload)
    lines = [
        "Shared Asset Compatibility",
        f"release_version={payload['release_version']}",
        " ".join(f"{key}={value}" for key, value in summary.items()),
    ]
    lines.extend(f"{item['status']}: {item['path']}" for item in payload["assets"])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect, stage, or safely apply shared scaffold asset upgrades.")
    parser.add_argument("command", choices=["report", "stage", "apply-safe", "resolve"])
    parser.add_argument("--vault-root", default=str(VAULT_ROOT))
    parser.add_argument("--source-root", default=str(DEFAULT_SOURCE_ROOT))
    parser.add_argument("--path", default="")
    parser.add_argument("--resolution", choices=sorted(RESOLUTION_VALUES), default="")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()
    release, assets = load_manifest(Path(args.source_root) / "00_system" / "registry" / "shared_assets.json")
    kwargs = {
        "vault_root": Path(args.vault_root),
        "source_root": Path(args.source_root),
        "release_version": release,
        "assets": assets,
    }
    if args.command == "resolve":
        if not args.path or not args.resolution:
            raise SystemExit("resolve requires --path and --resolution")
        payload = resolve_shared_asset(rel_path=args.path, resolution=args.resolution, **kwargs)
    elif args.command == "report":
        payload = inspect_shared_assets(**kwargs)
        payload["summary"] = summarize(payload)
    else:
        payload = apply_shared_asset_action(args.command, **kwargs)
    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.format == "json" else render_text(payload))


if __name__ == "__main__":
    main()
