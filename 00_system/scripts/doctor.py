from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import sqlite3
import sys
from pathlib import Path

from context_integrity import inspect_context


SCRIPT_DIR = Path(__file__).resolve().parent
SOURCE_ROOT = SCRIPT_DIR.parent.parent
REQUIRED_IMPORTS = {
    "yaml": "PyYAML",
    "pypdf": "pypdf",
    "docx": "python-docx",
    "pptx": "python-pptx",
}
WRAPPER_BASES = (
    "otw",
    "doctor",
    "attach_project",
    "project_session",
    "ingest_source",
    "source_quality",
    "search_wiki",
    "vault_compat",
    "shared_assets",
    "project_adapter",
)


def check(check_id: str, status: str, detail: str) -> dict[str, str]:
    return {"id": check_id, "status": status, "detail": detail}


def load_json_object(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("root value must be an object")
    return payload


def configured_wiki_root(repo_root: Path, explicit: str) -> Path | None:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    env_root = os.environ.get("OBSIDIAN_WIKI_ROOT", "").strip()
    if env_root:
        candidates.append(Path(env_root).expanduser())
    context_path = repo_root / "wiki.context.json"
    if context_path.exists():
        try:
            context = load_json_object(context_path)
            raw_root = str(context.get("wiki_root") or "").strip()
            if raw_root:
                candidates.append(Path(raw_root).expanduser())
        except (OSError, json.JSONDecodeError, ValueError):
            pass
    for config_path in (Path.home() / ".obsidiantowiki.json", Path.home() / ".config/obsidiantowiki/config.json"):
        if not config_path.exists():
            continue
        try:
            config = load_json_object(config_path)
        except (OSError, json.JSONDecodeError, ValueError):
            continue
        for key in ("default_wiki_root", "last_wiki_root"):
            raw_root = str(config.get(key) or "").strip()
            if raw_root:
                candidates.append(Path(raw_root).expanduser())
    candidates.append(repo_root.parent / "ObsidianToWiki-private")
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.exists() and resolved.is_dir():
            return resolved
    return None


def validate_policy(wiki_root: Path) -> tuple[str, str]:
    policy_path = wiki_root / "wiki.private.json"
    if not policy_path.exists():
        return "warn", "wiki.private.json is not configured; no ObsidianToWiki AI exclusions are active"
    try:
        payload = load_json_object(policy_path)
        ai_access = payload.get("ai_access")
        if payload.get("schema_version") != 1 or not isinstance(ai_access, dict):
            raise ValueError("schema_version=1 and ai_access object are required")
        for key in ("excluded_paths", "excluded_globs"):
            values = ai_access.get(key, [])
            if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
                raise ValueError(f"ai_access.{key} must be a string list")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return "fail", f"invalid wiki.private.json: {exc}"
    return "pass", f"valid policy at {policy_path}"


def validate_vault_state(wiki_root: Path) -> tuple[str, str]:
    schema_path = SOURCE_ROOT / "00_system" / "registry" / "vault_schema.json"
    state_path = wiki_root / "00_system" / "registry" / "vault_state.json"
    try:
        target = int(load_json_object(schema_path)["current_vault_version"])
    except (OSError, json.JSONDecodeError, ValueError, KeyError) as exc:
        return "fail", f"invalid runtime vault schema: {exc}"
    if not state_path.exists():
        return "warn", f"vault state is not initialized; target version is {target}"
    try:
        current = int(load_json_object(state_path)["vault_schema_version"])
    except (OSError, json.JSONDecodeError, ValueError, KeyError) as exc:
        return "fail", f"invalid vault state: {exc}"
    if current > target:
        return "fail", f"vault version {current} is newer than runtime target {target}"
    if current < target:
        return "warn", f"vault version {current} requires migration to {target}"
    return "pass", f"vault schema version {current} is current"


def validate_runtime_release() -> tuple[str, str]:
    release_path = SOURCE_ROOT / "00_system" / "registry" / "runtime_release.json"
    try:
        payload = load_json_object(release_path)
        version = str(payload.get("runtime_version") or "").strip()
        project_version = int(payload["project_scaffold_version"])
        private_version = int(payload["private_scaffold_version"])
        if payload.get("schema_version") != 1 or not version:
            raise ValueError("schema_version=1 and runtime_version are required")
    except (OSError, json.JSONDecodeError, ValueError, KeyError) as exc:
        return "fail", f"invalid runtime release manifest: {exc}"
    return "pass", f"runtime={version} private_scaffold={private_version} project_scaffold={project_version}"


def validate_private_scaffold_state(wiki_root: Path) -> tuple[str, str] | None:
    state_path = wiki_root / "00_system" / "registry" / "private_scaffold_state.json"
    if not state_path.exists():
        return None
    try:
        current = int(load_json_object(state_path)["private_scaffold_version"])
        target = int(load_json_object(SOURCE_ROOT / "00_system/registry/runtime_release.json")["private_scaffold_version"])
    except (OSError, json.JSONDecodeError, ValueError, KeyError) as exc:
        return "fail", f"invalid private scaffold state: {exc}"
    if current > target:
        return "fail", f"private scaffold {current} is newer than runtime target {target}"
    if current < target:
        return "warn", f"private scaffold {current} requires update to {target}"
    return "pass", f"private scaffold version {current} is current"


def run_checks(repo_root: Path, explicit_wiki_root: str) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    python_ok = sys.version_info >= (3, 10)
    results.append(
        check(
            "python",
            "pass" if python_ok else "fail",
            f"{platform.python_implementation()} {platform.python_version()} on {platform.system()}",
        )
    )
    for module, package in REQUIRED_IMPORTS.items():
        installed = importlib.util.find_spec(module) is not None
        results.append(check(f"dependency:{package}", "pass" if installed else "fail", "installed" if installed else "missing"))

    try:
        connection = sqlite3.connect(":memory:")
        connection.execute("CREATE VIRTUAL TABLE probe USING fts5(body)")
        connection.close()
        results.append(check("sqlite:fts5", "pass", f"SQLite {sqlite3.sqlite_version} with FTS5"))
    except sqlite3.Error as exc:
        results.append(check("sqlite:fts5", "fail", str(exc)))

    core_files = [
        SOURCE_ROOT / "PRODUCT_SPEC.md",
        SOURCE_ROOT / "00_system" / "registry" / "vault_schema.json",
        SOURCE_ROOT / "00_system" / "registry" / "memory_policy.json",
    ]
    missing_core = [path.relative_to(SOURCE_ROOT).as_posix() for path in core_files if not path.exists()]
    results.append(check("runtime", "fail" if missing_core else "pass", f"missing: {', '.join(missing_core)}" if missing_core else str(SOURCE_ROOT)))
    release_status, release_detail = validate_runtime_release()
    results.append(check("runtime_release", release_status, release_detail))

    missing_wrappers = [
        f"{base}{suffix}"
        for base in WRAPPER_BASES
        for suffix in (".py", ".ps1", ".sh")
        if not (SCRIPT_DIR / f"{base}{suffix}").exists()
    ]
    results.append(
        check(
            "cross_platform_wrappers",
            "fail" if missing_wrappers else "pass",
            f"missing: {', '.join(missing_wrappers)}" if missing_wrappers else "Python, PowerShell, and POSIX wrappers present",
        )
    )

    wiki_root = configured_wiki_root(repo_root, explicit_wiki_root)
    if wiki_root is None:
        results.append(check("wiki_root", "warn", "not configured; attach or provide a private wiki root"))
        return results
    results.append(check("wiki_root", "pass", str(wiki_root)))
    policy_status, policy_detail = validate_policy(wiki_root)
    results.append(check("privacy_policy", policy_status, policy_detail))
    state_status, state_detail = validate_vault_state(wiki_root)
    results.append(check("vault_schema", state_status, state_detail))
    private_scaffold = validate_private_scaffold_state(wiki_root)
    if private_scaffold is not None:
        results.append(check("private_scaffold", private_scaffold[0], private_scaffold[1]))

    context_path = repo_root / "wiki.context.json"
    if not context_path.exists():
        results.append(check("project_context", "pass", "current directory is not an attached project"))
    else:
        try:
            context = load_json_object(context_path)
            valid = bool(str(context.get("project_slug") or "").strip() and str(context.get("wiki_root") or "").strip())
            results.append(check("project_context", "pass" if valid else "fail", str(context_path)))
            if valid:
                target = int(load_json_object(SOURCE_ROOT / "00_system/registry/runtime_release.json")["project_scaffold_version"])
                current = int(context.get("project_scaffold_version") or 0)
                runtime_root = Path(str(context.get("runtime_root") or "")).expanduser()
                project_status = "pass" if current == target and runtime_root.resolve() == SOURCE_ROOT else "warn"
                detail = f"version={current}/{target} runtime_root={runtime_root or '<missing>'}"
                results.append(check("project_scaffold", project_status, detail))
                integrity = inspect_context(repo_root, [])
                integrity_status = str(integrity["status"])
                doctor_status = {
                    "trusted": "pass",
                    "review_required": "warn",
                    "degraded": "warn",
                    "quarantined": "fail",
                }[integrity_status]
                summary = integrity["summary"]
                results.append(check("context_integrity", doctor_status, f"status={integrity_status} summary={summary}"))
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            results.append(check("project_context", "fail", f"invalid wiki.context.json: {exc}"))
    return results


def render_text(payload: dict[str, object]) -> str:
    lines = [f"ObsidianToWiki Doctor: {payload['status']}"]
    lines.extend(f"[{item['status'].upper()}] {item['id']}: {item['detail']}" for item in payload["checks"])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnose an ObsidianToWiki installation without modifying it.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--wiki-root", default="")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as a non-zero result.")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()
    checks = run_checks(Path(args.repo_root).expanduser().resolve(), args.wiki_root)
    statuses = {item["status"] for item in checks}
    status = "fail" if "fail" in statuses or (args.strict and "warn" in statuses) else "pass"
    payload: dict[str, object] = {"schema_version": 1, "status": status, "strict": args.strict, "checks": checks}
    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.format == "json" else render_text(payload))
    if status == "fail":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
