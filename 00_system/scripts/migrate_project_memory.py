from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

from memory_compiler import CORE_PROJECTION_NAMES, compile_projections, write_text_atomic
from wiki_lib import parse_frontmatter, render_markdown


CORE_PAGE_NAMES = CORE_PROJECTION_NAMES
CONTROL_FILES = ("PRODUCT_SPEC.md", "ARCHITECTURE.md", "TASKS.md")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_context(repo_root: Path) -> tuple[Path, str]:
    path = repo_root / "wiki.context.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return Path(str(payload["wiki_root"])).expanduser().resolve(), str(payload["project_slug"])
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid wiki.context.json: {exc}") from exc


def page_body(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        _frontmatter, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        return body.strip()
    except ValueError:
        return path.read_text(encoding="utf-8").strip()


def classify_project(project_root: Path) -> str:
    paths = [project_root / name for name in CORE_PAGE_NAMES]
    total_bytes = sum(path.stat().st_size for path in paths if path.exists())
    if total_bytes > 100_000:
        return "long"
    meaningful = []
    for path in paths:
        body = page_body(path)
        body = "\n".join(line for line in body.splitlines() if not line.lstrip().startswith("#")).strip()
        if body and body not in {"待补充。", "暂无。", "TODO"}:
            meaningful.append(body)
    return "normal" if meaningful else "template"


def _snapshot_card(
    *, card_id: str, stable_key: str, summary: str, project_slug: str, evidence_ref: str, today: date
) -> str:
    frontmatter = {
        "title": summary,
        "type": "项目记忆卡",
        "domain": "项目",
        "project": project_slug,
        "tags": ["原子记忆", "迁移待复核"],
        "updated": today.isoformat(),
        "id": card_id,
        "stable_key": stable_key,
        "kind": "capability_observation",
        "status": "pending_review",
        "effective_from": today.isoformat(),
        "source_receipt": "memory-migration",
        "evidence_refs": [evidence_ref],
        "destination": "project",
        "review_reasons": ["legacy_content_requires_review"],
        "last_verified": today.isoformat(),
        "confidence": "review_required",
        "summary": summary,
    }
    return render_markdown(frontmatter, f"# {summary}\n\n{summary}\n\n来源：`{evidence_ref}`")


def _first_fact(path: Path) -> str:
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line and not line.startswith(("#", "---", "<!--")) and line not in {"待补充。", "暂无。"}:
            return line.lstrip("- ")[:240]
    return ""


def _existing_manifest(project_root: Path) -> tuple[Path, dict[str, Any] | None]:
    path = project_root / "memory" / "migration-manifest.json"
    if not path.exists():
        return path, None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return path, payload if isinstance(payload, dict) else None
    except json.JSONDecodeError:
        return path, None


def migrate_project_memory(
    repo_root: Path,
    *,
    apply: bool = False,
    wiki_root: Path | None = None,
    project_slug: str = "",
    today: date | None = None,
) -> dict[str, Any]:
    repo_root = repo_root.expanduser().resolve()
    today = today or date.today()
    if wiki_root is None or not project_slug:
        context_root, context_slug = read_context(repo_root)
        wiki_root = wiki_root or context_root
        project_slug = project_slug or context_slug
    wiki_root = wiki_root.expanduser().resolve()
    project_root = wiki_root / "20_projects" / "active" / project_slug
    classification = classify_project(project_root)
    manifest_path, existing = _existing_manifest(project_root)

    if existing:
        expected = existing.get("output_hashes") if isinstance(existing.get("output_hashes"), dict) else {}
        conflicts = [
            name
            for name, digest in expected.items()
            if not (project_root / name).exists() or file_hash(project_root / name) != digest
        ]
        if conflicts:
            return {"status": "conflict", "classification": classification, "conflicts": conflicts, "manifest": str(manifest_path)}
        return {"status": "unchanged", "classification": classification, "conflicts": [], "manifest": str(manifest_path)}

    source_paths = {name: project_root / name for name in CORE_PAGE_NAMES}
    source_hashes = {name: file_hash(path) for name, path in source_paths.items() if path.exists()}
    migration_key = json.dumps(source_hashes, sort_keys=True).encode("utf-8")
    migration_id = f"{today.isoformat()}-{hashlib.sha256(migration_key).hexdigest()[:12]}"
    report = {
        "status": "dry_run",
        "classification": classification,
        "migration_id": migration_id,
        "pages": list(CORE_PAGE_NAMES),
        "conflicts": [],
    }
    if not apply:
        return report

    archive_root = project_root / "memory" / "archive" / migration_id
    backups: dict[str, str] = {}
    archive_links: dict[str, str] = {}
    for name, source in source_paths.items():
        backup = archive_root / name
        backup.parent.mkdir(parents=True, exist_ok=True)
        backup.write_bytes(source.read_bytes() if source.exists() else b"")
        relative = backup.relative_to(project_root).as_posix()
        backups[name] = relative
        archive_links[name] = relative[:-3] if relative.endswith(".md") else relative

    memory_dir = project_root / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    if classification == "template":
        created = 0
        for file_name in CONTROL_FILES:
            control = repo_root / file_name
            if not control.exists():
                continue
            fact = _first_fact(control)
            if not fact:
                continue
            card_id = f"CONTROL-{Path(file_name).stem.upper()}"
            content = _snapshot_card(
                card_id=card_id,
                stable_key=f"initial-control-{file_name.lower()}",
                summary=fact,
                project_slug=project_slug,
                evidence_ref=f"repo:{file_name}",
                today=today,
            )
            write_text_atomic(memory_dir / f"{card_id}.md", content)
            created += 1
        if not created:
            content = _snapshot_card(
                card_id="CONTROL-INITIAL",
                stable_key="initial-project-snapshot",
                summary="Initial project snapshot requires human review.",
                project_slug=project_slug,
                evidence_ref="repo:wiki.context.json",
                today=today,
            )
            write_text_atomic(memory_dir / "CONTROL-INITIAL.md", content)
    else:
        for name in CORE_PAGE_NAMES:
            stem = hashlib.sha256(name.encode("utf-8")).hexdigest()[:10].upper()
            content = _snapshot_card(
                card_id=f"LEGACY-{stem}",
                stable_key=f"legacy-{name.lower()}",
                summary=f"Review legacy content from {name} before treating it as current fact.",
                project_slug=project_slug,
                evidence_ref=f"wiki:{archive_links[name]}",
                today=today,
            )
            write_text_atomic(memory_dir / f"LEGACY-{stem}.md", content)

    projection = compile_projections(
        wiki_root=wiki_root,
        project_slug=project_slug,
        dry_run=False,
        today=today,
        archive_links=archive_links,
        allow_unmanaged=True,
    )
    output_hashes = {name: file_hash(project_root / name) for name in CORE_PAGE_NAMES}
    manifest = {
        "schema_version": 1,
        "migration_id": migration_id,
        "project_slug": project_slug,
        "classification": classification,
        "created": today.isoformat(),
        "source_hashes": source_hashes,
        "output_hashes": output_hashes,
        "backups": backups,
        "projection_pages": [page["name"] for page in projection["pages"]],
    }
    write_text_atomic(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return {**report, "status": "applied", "manifest": str(manifest_path)}


def restore_migration(manifest_path: Path) -> dict[str, Any]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    project_root = manifest_path.parent.parent
    backups = payload.get("backups") if isinstance(payload.get("backups"), dict) else {}
    for name, relative in backups.items():
        source = project_root / str(relative)
        destination = project_root / str(name)
        destination.write_bytes(source.read_bytes())
    return {"status": "restored", "pages": sorted(backups)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect or apply bounded project-memory migration.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--restore", default="", help="Restore from a migration manifest path.")
    args = parser.parse_args()
    if sum(bool(value) for value in (args.dry_run, args.apply, args.restore)) != 1:
        raise SystemExit("choose exactly one of --dry-run, --apply, or --restore")
    if args.restore:
        report = restore_migration(Path(args.restore).expanduser().resolve())
    else:
        report = migrate_project_memory(Path(args.repo_root), apply=args.apply)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
