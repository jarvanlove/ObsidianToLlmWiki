from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

from project_adapter import inspect_adapter
from schema_lib import load_schema_registry, validate_page_schema
from shared_assets import inspect_shared_assets, load_manifest, summarize
from wiki_lib import (
    SCRIPT_DIR,
    VAULT_ROOT,
    is_ai_access_excluded,
    iter_markdown_files,
    load_page,
    load_private_policy,
    now_iso,
)


VAULT_SCHEMA_PATH = SCRIPT_DIR.parent / "registry" / "vault_schema.json"
VAULT_STATE_PATH = VAULT_ROOT / "00_system" / "registry" / "vault_state.json"
PROJECTS_REGISTRY_PATH = VAULT_ROOT / "00_system" / "registry" / "projects.json"


def load_json_object(path: Path, *, required: bool = False) -> dict[str, object]:
    if not path.exists():
        if required:
            raise SystemExit(f"required JSON file is missing: {path}")
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"cannot read JSON file {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit(f"JSON file must contain an object: {path}")
    return payload


def load_vault_schema() -> dict[str, object]:
    payload = load_json_object(VAULT_SCHEMA_PATH, required=True)
    if payload.get("schema_version") != 1:
        raise SystemExit("vault_schema.json requires schema_version=1")
    target = payload.get("current_vault_version")
    migrations = payload.get("migrations")
    if not isinstance(target, int) or target < 1 or not isinstance(migrations, list):
        raise SystemExit("vault_schema.json has an invalid target version or migrations list")
    return payload


def load_vault_state() -> dict[str, object]:
    if not VAULT_STATE_PATH.exists():
        return {"schema_version": 1, "vault_schema_version": 0, "migration_history": []}
    payload = load_json_object(VAULT_STATE_PATH)
    if payload.get("schema_version") != 1:
        raise SystemExit("vault_state.json requires schema_version=1")
    version = payload.get("vault_schema_version")
    history = payload.get("migration_history")
    if not isinstance(version, int) or version < 0 or not isinstance(history, list):
        raise SystemExit("vault_state.json has an invalid vault version or migration history")
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


def migrations_after(current: int, schema: dict[str, object]) -> list[dict[str, object]]:
    pending: list[dict[str, object]] = []
    cursor = current
    migrations = schema["migrations"]
    for migration in migrations:
        if not isinstance(migration, dict):
            raise SystemExit("vault_schema.json contains a non-object migration")
        from_version = migration.get("from_version")
        to_version = migration.get("to_version")
        migration_id = str(migration.get("id") or "").strip()
        if not migration_id or not isinstance(from_version, int) or not isinstance(to_version, int):
            raise SystemExit("vault_schema.json contains an invalid migration")
        if from_version == cursor:
            if to_version <= from_version:
                raise SystemExit(f"migration {migration_id} does not advance the vault version")
            pending.append(migration)
            cursor = to_version
    target = int(schema["current_vault_version"])
    if cursor != target:
        raise SystemExit(f"no complete migration chain from vault version {current} to {target}")
    return pending


def registered_projects() -> list[dict[str, object]]:
    if not PROJECTS_REGISTRY_PATH.exists():
        return []
    try:
        payload = json.loads(PROJECTS_REGISTRY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"cannot read projects registry: {exc}") from exc
    return [item for item in payload if isinstance(item, dict)] if isinstance(payload, list) else []


def wiki_project_slugs() -> list[str]:
    slugs: set[str] = set()
    for state in ("active", "archive"):
        root = VAULT_ROOT / "20_projects" / state
        if not root.exists():
            continue
        for child in root.iterdir():
            if child.is_dir() and (child / "索引.md").exists():
                slugs.add(child.name)
    return sorted(slugs)


def compatibility_report() -> dict[str, object]:
    schema = load_vault_schema()
    state = load_vault_state()
    current = int(state["vault_schema_version"])
    target = int(schema["current_vault_version"])
    if current > target:
        raise SystemExit(f"vault schema version {current} is newer than this runtime target {target}")
    pending = migrations_after(current, schema)

    policy = load_private_policy()
    all_markdown = list(VAULT_ROOT.rglob("*.md"))
    excluded_markdown = sum(1 for path in all_markdown if is_ai_access_excluded(path, policy=policy))
    pages = [load_page(path) for path in iter_markdown_files()]
    registry = load_schema_registry()
    schema_issues: list[dict[str, object]] = []
    for page in pages:
        errors = validate_page_schema(page, registry)
        if errors:
            schema_issues.append({"path": str(page["rel_path"]), "errors": errors})

    projects = registered_projects()
    registered_slugs = sorted(
        {str(item.get("project_slug") or "").strip() for item in projects if str(item.get("project_slug") or "").strip()}
    )
    wiki_slugs = wiki_project_slugs()
    repo_status = []
    for item in projects:
        repo_root = Path(str(item.get("project_repo_root") or "")).expanduser()
        adapter_status = "repo_missing"
        adapter_version = 0
        if repo_root.exists():
            try:
                adapter_report = inspect_adapter(repo_root)
                adapter_status = str(adapter_report["status"])
                adapter_version = int(adapter_report["adapter_version"])
            except RuntimeError as exc:
                adapter_status = f"error: {exc}"
        repo_status.append(
            {
                "project_slug": str(item.get("project_slug") or ""),
                "repo_root": str(repo_root),
                "repo_exists": repo_root.exists(),
                "wiki_context_exists": (repo_root / "wiki.context.json").exists() if repo_root.exists() else False,
                "adapter_status": adapter_status,
                "adapter_version": adapter_version,
            }
        )

    shared_assets: dict[str, object]
    try:
        release_version, asset_manifest = load_manifest()
        shared_assets = inspect_shared_assets(
            vault_root=VAULT_ROOT,
            source_root=SCRIPT_DIR.parent.parent,
            release_version=release_version,
            assets=asset_manifest,
        )
        shared_assets["summary"] = summarize(shared_assets)
    except RuntimeError as exc:
        shared_assets = {"status": "unavailable", "error": str(exc)}

    return {
        "schema_version": 1,
        "vault_root": str(VAULT_ROOT),
        "vault_schema": {
            "current": current,
            "target": target,
            "pending_migrations": [str(item["id"]) for item in pending],
            "state_path": VAULT_STATE_PATH.relative_to(VAULT_ROOT).as_posix(),
        },
        "privacy": {
            "policy_present": (VAULT_ROOT / "wiki.private.json").exists(),
            "excluded_markdown_pages": excluded_markdown,
        },
        "pages": {
            "indexed_candidates": len(pages),
            "schema_issue_count": len(schema_issues),
            "schema_issues": schema_issues,
        },
        "wiki_projects": {
            "registered": registered_slugs,
            "unregistered": sorted(set(wiki_slugs) - set(registered_slugs)),
            "registry_only": sorted(set(registered_slugs) - set(wiki_slugs)),
            "repositories": repo_status,
        },
        "shared_assets": shared_assets,
    }


def migrate(*, apply: bool) -> dict[str, object]:
    schema = load_vault_schema()
    state = load_vault_state()
    current = int(state["vault_schema_version"])
    target = int(schema["current_vault_version"])
    if current > target:
        raise SystemExit(f"vault schema version {current} is newer than this runtime target {target}")
    pending = migrations_after(current, schema)
    applied: list[str] = []
    if apply and pending:
        history = list(state.get("migration_history") or [])
        for migration in pending:
            migration_id = str(migration["id"])
            history.append(
                {
                    "id": migration_id,
                    "from_version": migration["from_version"],
                    "to_version": migration["to_version"],
                    "applied_at": now_iso(),
                }
            )
            state["vault_schema_version"] = migration["to_version"]
            applied.append(migration_id)
        state["schema_version"] = 1
        state["migration_history"] = history
        write_json_atomic(VAULT_STATE_PATH, state)
    return {
        "schema_version": 1,
        "apply": apply,
        "from_version": current,
        "to_version": int(state["vault_schema_version"]) if apply else current,
        "target_version": target,
        "planned": [str(item["id"]) for item in pending],
        "applied": applied,
        "state_path": VAULT_STATE_PATH.relative_to(VAULT_ROOT).as_posix(),
    }


def render_text(payload: dict[str, object]) -> str:
    if "vault_schema" in payload:
        schema = payload["vault_schema"]
        pages = payload["pages"]
        projects = payload["wiki_projects"]
        shared_assets = payload["shared_assets"]
        shared_summary = shared_assets.get("summary", {}) if isinstance(shared_assets, dict) else {}
        return "\n".join(
            [
                "Vault Compatibility Report",
                f"vault_version={schema['current']} target={schema['target']}",
                f"pending={','.join(schema['pending_migrations']) or '-'}",
                f"pages={pages['indexed_candidates']} schema_issues={pages['schema_issue_count']}",
                f"unregistered_projects={','.join(projects['unregistered']) or '-'}",
                "shared_assets="
                + " ".join(f"{key}:{value}" for key, value in shared_summary.items())
                if shared_summary
                else "shared_assets=unavailable",
            ]
        )
    return "\n".join(
        [
            "Vault Migration",
            f"apply={str(payload['apply']).lower()}",
            f"from={payload['from_version']} to={payload['to_version']} target={payload['target_version']}",
            f"applied={','.join(payload['applied']) or '-'}",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit and migrate ObsidianToWiki vault compatibility state.")
    parser.add_argument("command", choices=["report", "migrate"])
    parser.add_argument("--apply", action="store_true", help="Apply pending metadata-only migrations.")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    payload = compatibility_report() if args.command == "report" else migrate(apply=args.apply)
    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.format == "json" else render_text(payload))


if __name__ == "__main__":
    main()
