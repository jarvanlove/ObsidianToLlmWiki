from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SOURCE_ROOT = SCRIPT_DIR.parent.parent
STATE_REL_PATH = Path("00_system/registry/private_scaffold_state.json")
CANDIDATE_REL_ROOT = Path("40_outputs/upgrade-candidates/private-scaffold")
BACKUP_REL_ROOT = Path("40_outputs/update-backups")
TEXT_EXTENSIONS = {".md", ".py", ".ps1", ".sh", ".json", ".txt", ".yml", ".yaml", ".html"}
DEFAULT_MANIFEST = {
    "categories": {
        "root": [
            "README.md",
            "README-zh.md",
            "快速开始.md",
            "标准自然语言话术清单.md",
            "使用手册.md",
            "会话启动页.md",
        ],
        "system": [
            "00_system/registry/page_schemas.json",
            "00_system/registry/ingestion_quality.json",
            "00_system/registry/private_sync_manifest.json",
            "00_system/registry/project_adapter_schema.json",
            "00_system/registry/project_scaffold_schema.json",
            "00_system/registry/retrieval_aliases.json",
            "00_system/registry/retrieval_eval_cases.json",
            "00_system/registry/runtime_release.json",
            "00_system/registry/shared_assets.json",
            "00_system/registry/vault_schema.json",
            "00_system/requirements.txt",
            "00_system/requirements-mcp.txt",
            "00_system/scripts",
            "00_system/templates",
        ],
        "docs": ["docs"],
        "prompts": ["30_shared/prompts"],
    },
    "ignore_globs": [
        "**/__pycache__/**",
        "**/*.pyc",
        "**/.cache/**",
        "**/*.sqlite3",
        "**/*.sqlite3-shm",
        "**/*.sqlite3-wal",
    ],
    "protected_globs": [
        "AGENTS.md",
        "CLAUDE.md",
        "Home.md",
        "index.md",
        "log.md",
        "wiki.private.json",
        STATE_REL_PATH.as_posix(),
        "00_system/registry/runtime_update_receipt.json",
        "00_system/registry/projects.json",
        "00_system/registry/vault_state.json",
        "00_system/.cache/**",
        "01_inbox/**",
        "10_personal/**",
        "20_projects/**",
        "30_shared/architectures/**",
        "30_shared/patterns/**",
        "30_shared/tools/**",
        "30_shared/索引.md",
        "30_shared/关系索引.md",
        "40_outputs/**",
    ],
}


def default_private_root(source_root: Path = SOURCE_ROOT) -> Path:
    return source_root.parent / f"{source_root.name}-private"


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def baseline_equivalent(source: Path, destination: Path) -> bool:
    if source.read_bytes() == destination.read_bytes():
        return True
    if source.suffix.lower() not in TEXT_EXTENSIONS:
        return False
    try:
        source_text = source.read_text(encoding="utf-8").replace("\r\n", "\n")
        destination_text = destination.read_text(encoding="utf-8").replace("\r\n", "\n")
    except UnicodeDecodeError:
        return False
    return source_text == destination_text


def write_atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
        os.replace(temp_name, path)
    finally:
        temporary = Path(temp_name)
        if temporary.exists():
            temporary.unlink()


def load_json_object(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def load_manifest(source_root: Path) -> dict[str, object]:
    payload = load_json_object(source_root / "00_system" / "registry" / "private_sync_manifest.json")
    return payload or DEFAULT_MANIFEST


def should_ignore(path: Path, globs: list[str]) -> bool:
    normalized = path.as_posix()
    return any(path.match(pattern) or Path(normalized).match(pattern) for pattern in globs)


def normalized_relative_path(raw_path: str) -> Path:
    normalized = raw_path.strip().replace("\\", "/")
    path = Path(normalized)
    if not normalized or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"invalid relative path: {raw_path}")
    return path


def is_managed_path(path: Path, managed_roots: list[Path]) -> bool:
    return any(path == root or root in path.parents for root in managed_roots)


def selected_managed_roots(
    manifest: dict[str, object], only: list[str] | None, requested_paths: list[str] | None
) -> tuple[list[Path], list[str], list[str]]:
    categories = manifest.get("categories") if isinstance(manifest.get("categories"), dict) else {}
    all_roots: list[Path] = []
    for values in categories.values():
        if isinstance(values, list):
            all_roots.extend(normalized_relative_path(str(value)) for value in values)
    protected = [str(value) for value in manifest.get("protected_globs", []) if str(value).strip()]
    if requested_paths:
        selected: list[Path] = []
        for value in requested_paths:
            path = normalized_relative_path(value)
            if should_ignore(path, protected):
                raise ValueError(f"protected path: {path.as_posix()}")
            if not is_managed_path(path, all_roots):
                raise ValueError(f"path is outside managed scaffold: {path.as_posix()}")
            selected.append(path)
        return selected, [], protected

    selected_categories = only or list(categories.keys())
    selected = []
    for category in selected_categories:
        values = categories.get(category, [])
        if isinstance(values, list):
            selected.extend(normalized_relative_path(str(value)) for value in values)
    return selected, selected_categories, protected


def iter_source_files(
    source_root: Path,
    roots: list[Path],
    ignore_globs: list[str],
    protected_globs: list[str],
) -> list[tuple[Path, Path]]:
    files: dict[str, tuple[Path, Path]] = {}
    for root in roots:
        source = source_root / root
        candidates = [source] if source.is_file() else source.rglob("*") if source.is_dir() else []
        for candidate in candidates:
            if not candidate.is_file():
                continue
            relative = candidate.relative_to(source_root)
            if should_ignore(relative, ignore_globs) or should_ignore(relative, protected_globs):
                continue
            files[relative.as_posix()] = (candidate, relative)
    return [files[key] for key in sorted(files)]


def load_state(private_root: Path) -> dict[str, object]:
    state = load_json_object(private_root / STATE_REL_PATH)
    if not isinstance(state.get("managed_hashes"), dict):
        state["managed_hashes"] = {}
    return state


def save_state(private_root: Path, state: dict[str, object]) -> None:
    payload = {
        "schema_version": 1,
        "private_scaffold_version": 1,
        "updated_at": datetime.now().replace(microsecond=0).isoformat(),
        "managed_hashes": state.get("managed_hashes", {}),
    }
    write_atomic(private_root / STATE_REL_PATH, (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def record_matching_baseline(
    source_root: Path,
    private_root: Path,
    files: list[tuple[Path, Path]],
    *,
    dry_run: bool,
) -> list[dict[str, str]]:
    state = load_state(private_root)
    hashes = state["managed_hashes"]
    assert isinstance(hashes, dict)
    actions: list[dict[str, str]] = []
    for source, relative in files:
        destination = private_root / relative
        if not destination.exists() or not baseline_equivalent(source, destination):
            continue
        digest = file_sha256(destination)
        hashes[relative.as_posix()] = digest
        actions.append({"action": "baseline_recorded", "path": relative.as_posix()})
    if not dry_run:
        save_state(private_root, state)
    return actions


def sync_file(
    source: Path,
    destination: Path,
    relative: Path,
    private_root: Path,
    baseline_hash: str,
    *,
    dry_run: bool,
    backup_stamp: str,
) -> tuple[dict[str, str], str | None]:
    source_hash = file_sha256(source)
    rel_text = relative.as_posix()
    if not destination.exists():
        action = {"action": "create", "path": rel_text}
        if not dry_run:
            write_atomic(destination, source.read_bytes())
        return action, source_hash

    destination_hash = file_sha256(destination)
    if destination_hash == source_hash:
        return {"action": "skip", "path": rel_text}, source_hash
    if baseline_hash and destination_hash == baseline_hash:
        if not dry_run:
            write_atomic(destination, source.read_bytes())
        return {"action": "update", "path": rel_text}, source_hash

    candidate = private_root / CANDIDATE_REL_ROOT / Path(rel_text + ".new")
    backup = private_root / BACKUP_REL_ROOT / backup_stamp / relative
    if not dry_run:
        write_atomic(candidate, source.read_bytes())
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(destination, backup)
    return {
        "action": "conflict_staged",
        "path": rel_text,
        "candidate": candidate.relative_to(private_root).as_posix(),
        "backup": backup.relative_to(private_root).as_posix(),
    }, None


def sync_private_vault(
    source_root: Path,
    private_root: Path,
    *,
    dry_run: bool = False,
    only: list[str] | None = None,
    requested_paths: list[str] | None = None,
    initialize: bool = False,
    record_baseline: bool = False,
) -> dict[str, object]:
    source_root = source_root.expanduser().resolve()
    private_root = private_root.expanduser().resolve()
    if not source_root.exists():
        raise ValueError(f"public runtime does not exist: {source_root}")
    if not private_root.exists():
        if not initialize or dry_run:
            raise ValueError(f"private vault does not exist: {private_root}")
        private_root.mkdir(parents=True)

    manifest = load_manifest(source_root)
    roots, selected_categories, protected = selected_managed_roots(manifest, only, requested_paths)
    ignore = [str(value) for value in manifest.get("ignore_globs", []) if str(value).strip()]
    files = iter_source_files(source_root, roots, ignore, protected)
    if record_baseline:
        actions = record_matching_baseline(source_root, private_root, files, dry_run=dry_run)
    else:
        state = load_state(private_root)
        hashes = state["managed_hashes"]
        assert isinstance(hashes, dict)
        backup_stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        actions = []
        for source, relative in files:
            action, managed_hash = sync_file(
                source,
                private_root / relative,
                relative,
                private_root,
                str(hashes.get(relative.as_posix()) or ""),
                dry_run=dry_run,
                backup_stamp=backup_stamp,
            )
            actions.append(action)
            if managed_hash:
                hashes[relative.as_posix()] = managed_hash
        if not dry_run:
            save_state(private_root, state)

    summary = {
        "created": sum(1 for item in actions if item["action"] == "create"),
        "updated": sum(1 for item in actions if item["action"] == "update"),
        "skipped": sum(1 for item in actions if item["action"] == "skip"),
        "conflict_staged": sum(1 for item in actions if item["action"] == "conflict_staged"),
        "baseline_recorded": sum(1 for item in actions if item["action"] == "baseline_recorded"),
    }
    return {
        "source_root": str(source_root),
        "private_root": str(private_root),
        "dry_run": dry_run,
        "categories": selected_categories,
        "requested_paths": requested_paths or [],
        "record_baseline": record_baseline,
        "summary": summary,
        "actions": actions,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Safely synchronize the public scaffold into a private vault.")
    parser.add_argument("--source-root", default=str(SOURCE_ROOT), help="Public ObsidianToWiki runtime root.")
    parser.add_argument("--private-root", default="", help="Private vault root.")
    parser.add_argument("--initialize", action="store_true", help="Create the private root when it does not exist.")
    parser.add_argument("--record-baseline", action="store_true", help="Record hashes only for files already identical on both sides.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--only", action="append", choices=["root", "system", "docs", "prompts"])
    parser.add_argument("--path", action="append")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()
    if args.only and args.path:
        parser.error("--only and --path cannot be used together")

    source_root = Path(args.source_root)
    private_root = Path(args.private_root) if args.private_root else default_private_root(source_root)
    try:
        payload = sync_private_vault(
            source_root,
            private_root,
            dry_run=args.dry_run,
            only=args.only,
            requested_paths=args.path,
            initialize=args.initialize,
            record_baseline=args.record_baseline,
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(f"source_root={payload['source_root']}")
    print(f"private_root={payload['private_root']}")
    for action in payload["actions"]:
        suffix = f" -> {action['candidate']}" if action.get("candidate") else ""
        print(f"{action['action']}: {action['path']}{suffix}")
    summary = payload["summary"]
    print(" ".join(f"{key}={summary[key]}" for key in ("created", "updated", "skipped", "conflict_staged")))


if __name__ == "__main__":
    main()
