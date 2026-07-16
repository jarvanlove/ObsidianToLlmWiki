from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

from attach_project import (
    MANAGED_BLOCK_START,
    ensure_project_control_files,
    load_registry,
    render_context,
    render_managed_block,
    render_template,
    upsert_marked_block,
)


SCRIPT_DIR = Path(__file__).resolve().parent
SOURCE_ROOT = SCRIPT_DIR.parent.parent
SCHEMA_PATH = SOURCE_ROOT / "00_system" / "registry" / "project_scaffold_schema.json"
STATE_REL_PATH = Path(".obsidiantowiki/project-scaffold-state.json")
CANDIDATE_REL_ROOT = Path(".obsidiantowiki/upgrade-candidates/project-scaffold")
LIFECYCLE_PATH = Path("docs/ai-workflows/AI_CODING_LIFECYCLE.md")


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized_text_hash(text: str) -> str:
    return hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()


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


def load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def current_version(source_root: Path = SOURCE_ROOT) -> int:
    schema = load_json(source_root / "00_system" / "registry" / "project_scaffold_schema.json")
    return int(schema.get("current_project_scaffold_version") or 1)


def known_lifecycle_hashes(source_root: Path) -> set[str]:
    schema = load_json(source_root / "00_system" / "registry" / "project_scaffold_schema.json")
    managed = schema.get("managed_files") if isinstance(schema.get("managed_files"), dict) else {}
    entry = managed.get(LIFECYCLE_PATH.as_posix()) if isinstance(managed, dict) else {}
    values = entry.get("legacy_hashes") if isinstance(entry, dict) else []
    return {str(value).lower() for value in values if str(value).strip()}


def known_file_hashes(source_root: Path, relative_path: str) -> set[str]:
    schema = load_json(source_root / "00_system" / "registry" / "project_scaffold_schema.json")
    managed = schema.get("managed_files") if isinstance(schema.get("managed_files"), dict) else {}
    entry = managed.get(relative_path) if isinstance(managed, dict) else {}
    values = entry.get("legacy_hashes") if isinstance(entry, dict) else []
    return {str(value).lower() for value in values if str(value).strip()}


def upsert_project_entry(path: Path, block: str, source_root: Path) -> str:
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        prefix = existing.split(MANAGED_BLOCK_START, 1)[0].rstrip() if MANAGED_BLOCK_START in existing else existing.rstrip()
        if normalized_text_hash(prefix + "\n") in known_file_hashes(source_root, path.name):
            write_atomic(path, block.encode("utf-8"))
            return "legacy_migrated"
    return upsert_marked_block(path, block)


def load_context(repo_root: Path) -> dict[str, object]:
    return load_json(repo_root / "wiki.context.json")


def project_name(wiki_root: Path, project_slug: str, repo_root: Path) -> str:
    for item in load_registry(wiki_root):
        if str(item.get("project_slug") or "") == project_slug:
            return str(item.get("project_name") or repo_root.name)
    return repo_root.name


def safe_update_lifecycle(repo_root: Path, source_root: Path, state: dict[str, object]) -> dict[str, str]:
    destination = repo_root / LIFECYCLE_PATH
    candidate = repo_root / CANDIDATE_REL_ROOT / Path(LIFECYCLE_PATH.as_posix() + ".new")
    desired = (render_template("AI_CODING_LIFECYCLE.md", {}).rstrip() + "\n").encode("utf-8")
    desired_hash = hashlib.sha256(desired).hexdigest()
    desired_text_hash = normalized_text_hash(desired.decode("utf-8"))
    managed_hashes = state.setdefault("managed_hashes", {})
    assert isinstance(managed_hashes, dict)
    previous_hash = str(managed_hashes.get(LIFECYCLE_PATH.as_posix()) or "")
    current_hash = file_sha256(destination) if destination.exists() else ""
    current_text_hash = normalized_text_hash(destination.read_text(encoding="utf-8")) if destination.exists() else ""
    known_hashes = known_lifecycle_hashes(source_root)

    if current_hash == desired_hash or current_text_hash == desired_text_hash:
        action = "current"
    elif not destination.exists() or current_hash == previous_hash or current_text_hash.lower() in known_hashes:
        write_atomic(destination, desired)
        action = "created" if not current_hash else "updated"
    else:
        if not candidate.exists() or candidate.read_bytes() != desired:
            write_atomic(candidate, desired)
        return {"path": LIFECYCLE_PATH.as_posix(), "action": "conflict_staged", "candidate": str(candidate)}

    managed_hashes[LIFECYCLE_PATH.as_posix()] = file_sha256(destination)
    result = {"path": LIFECYCLE_PATH.as_posix(), "action": action}
    if candidate.exists() and hashlib.sha256(candidate.read_bytes()).hexdigest() == desired_hash:
        candidate.unlink()
        result["stale_candidate"] = "removed"
    return result


def apply_project_scaffold(repo_root: Path, source_root: Path = SOURCE_ROOT) -> dict[str, object]:
    repo_root = repo_root.expanduser().resolve()
    source_root = source_root.expanduser().resolve()
    context = load_context(repo_root)
    if not context:
        return {"repo_root": str(repo_root), "status": "not_attached", "actions": []}
    wiki_root = Path(str(context.get("wiki_root") or "")).expanduser().resolve()
    project_slug = str(context.get("project_slug") or "").strip()
    if not project_slug or not wiki_root.exists():
        return {"repo_root": str(repo_root), "status": "invalid_context", "actions": []}

    version = current_version(source_root)
    name = project_name(wiki_root, project_slug, repo_root)
    actions: list[dict[str, str]] = []
    for path, action in ensure_project_control_files(repo_root, name, project_slug).items():
        if action == "created":
            actions.append({"path": path, "action": action})

    for file_name in ("AGENTS.md", "CLAUDE.md"):
        action = upsert_project_entry(
            repo_root / file_name,
            render_managed_block(file_name, repo_root, wiki_root, project_slug),
            source_root,
        )
        actions.append({"path": file_name, "action": action})

    desired_context = json.loads(render_context(repo_root, wiki_root, project_slug))
    desired_context.update({key: value for key, value in context.items() if key not in desired_context})
    desired_context["runtime_root"] = str(source_root)
    desired_context["project_scaffold_version"] = version
    context_content = (json.dumps(desired_context, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    context_path = repo_root / "wiki.context.json"
    context_action = "current"
    if not context_path.exists() or context_path.read_bytes() != context_content:
        write_atomic(context_path, context_content)
        context_action = "updated"
    actions.append({"path": "wiki.context.json", "action": context_action})

    state = load_json(repo_root / STATE_REL_PATH)
    previous_state = json.loads(json.dumps(state))
    actions.append(safe_update_lifecycle(repo_root, source_root, state))
    state.update(
        {
            "schema_version": 1,
            "project_scaffold_version": version,
            "runtime_root": str(source_root),
        }
    )
    previous_state.pop("updated_at", None)
    comparable_state = dict(state)
    comparable_state.pop("updated_at", None)
    if comparable_state != previous_state:
        state["updated_at"] = datetime.now().replace(microsecond=0).isoformat()
        write_atomic(repo_root / STATE_REL_PATH, (json.dumps(state, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))

    changed_actions = {"created", "updated", "appended", "legacy_migrated"}
    status = "updated" if any(item["action"] in changed_actions for item in actions) else "current"
    return {"repo_root": str(repo_root), "status": status, "version": version, "actions": actions}


def registered_repo_roots(wiki_root: Path) -> list[Path]:
    roots: list[Path] = []
    for item in load_registry(wiki_root):
        raw = str(item.get("project_repo_root") or "").strip()
        if raw:
            roots.append(Path(raw).expanduser().resolve())
    return list(dict.fromkeys(roots))


def upgrade_registered_projects(wiki_root: Path, source_root: Path = SOURCE_ROOT) -> list[dict[str, object]]:
    reports: list[dict[str, object]] = []
    for repo_root in registered_repo_roots(wiki_root):
        if not repo_root.exists():
            reports.append({"repo_root": str(repo_root), "status": "missing", "actions": []})
            continue
        reports.append(apply_project_scaffold(repo_root, source_root))
    return reports


def main() -> None:
    parser = argparse.ArgumentParser(description="Safely upgrade the core bridge of attached projects.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--wiki-root", default="")
    parser.add_argument("--source-root", default=str(SOURCE_ROOT))
    parser.add_argument("--all-projects", action="store_true")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()
    source_root = Path(args.source_root)
    if args.all_projects:
        if not args.wiki_root:
            raise SystemExit("--wiki-root is required with --all-projects")
        reports = upgrade_registered_projects(Path(args.wiki_root).expanduser().resolve(), source_root)
    else:
        reports = [apply_project_scaffold(Path(args.repo_root), source_root)]
    payload = {"schema_version": 1, "reports": reports}
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    for report in reports:
        print(f"{report['status']}: {report['repo_root']}")
        for action in report.get("actions", []):
            print(f"  {action['action']}: {action['path']}")


if __name__ == "__main__":
    main()
