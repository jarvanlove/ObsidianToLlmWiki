from __future__ import annotations

import argparse
import filecmp
import json
import shutil
from pathlib import Path

from wiki_lib import VAULT_ROOT

MANIFEST_PATH = VAULT_ROOT / "00_system" / "registry" / "private_sync_manifest.json"
DEFAULT_MANIFEST = {
    "categories": {
        "root": [
            "AGENTS.md",
            "CLAUDE.md",
            "README.md",
            "README-zh.md",
            "快速开始.md",
            "标准自然语言话术清单.md",
            "使用手册.md",
            "会话启动页.md",
        ],
        "system": [
            "00_system/registry/page_schemas.json",
            "00_system/registry/private_sync_manifest.json",
            "00_system/registry/project_adapter_schema.json",
            "00_system/registry/retrieval_aliases.json",
            "00_system/registry/retrieval_eval_cases.json",
            "00_system/registry/shared_assets.json",
            "00_system/registry/vault_schema.json",
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
        "Home.md",
        "index.md",
        "log.md",
        "wiki.private.json",
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


def default_private_root() -> Path:
    return VAULT_ROOT.parent / f"{VAULT_ROOT.name}-private"


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def load_manifest() -> dict[str, object]:
    if not MANIFEST_PATH.exists():
        return DEFAULT_MANIFEST
    try:
        payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return DEFAULT_MANIFEST
    if not isinstance(payload, dict):
        return DEFAULT_MANIFEST
    return payload


def should_ignore(path: Path, ignore_globs: list[str]) -> bool:
    normalized = path.as_posix()
    return any(path.match(pattern) or Path(normalized).match(pattern) for pattern in ignore_globs)


def copy_file(src: Path, dst: Path, *, rel_path: str, dry_run: bool) -> dict[str, str]:
    if dst.exists() and filecmp.cmp(src, dst, shallow=False):
        action = "skip"
    else:
        action = "update" if dst.exists() else "create"
    if not dry_run and action != "skip":
        ensure_parent(dst)
        shutil.copy2(src, dst)
    return {"action": action, "path": rel_path}


def sync_tree(
    src_root: Path,
    dst_root: Path,
    *,
    dry_run: bool,
    ignore_globs: list[str],
    protected_globs: list[str],
) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    if not src_root.exists():
        return actions
    for src in src_root.rglob("*"):
        if src.is_dir():
            continue
        vault_rel = src.relative_to(VAULT_ROOT)
        if should_ignore(vault_rel, ignore_globs) or should_ignore(vault_rel, protected_globs):
            continue
        rel = src.relative_to(src_root)
        dst = dst_root / rel
        actions.append(copy_file(src, dst, rel_path=vault_rel.as_posix(), dry_run=dry_run))
    return actions


def normalized_relative_path(raw_path: str) -> Path:
    normalized = raw_path.strip().replace("\\", "/")
    path = Path(normalized)
    if not normalized or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"invalid relative path: {raw_path}")
    return path


def is_managed_path(path: Path, managed_roots: list[Path]) -> bool:
    for root in managed_roots:
        if path == root or root in path.parents:
            return True
    return False


def summary_for(actions: list[dict[str, str]]) -> dict[str, int]:
    return {
        "created": sum(1 for item in actions if item["action"] == "create"),
        "updated": sum(1 for item in actions if item["action"] == "update"),
        "skipped": sum(1 for item in actions if item["action"] == "skip"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="把公开脚手架的系统层同步到私有 vault。")
    parser.add_argument("--private-root", default=str(default_private_root()), help="私有 vault 根目录")
    parser.add_argument("--dry-run", action="store_true", help="只显示将要同步的内容，不实际写入")
    parser.add_argument("--only", action="append", choices=["root", "system", "docs", "prompts"], help="只同步指定类别，可重复传入")
    parser.add_argument("--path", action="append", help="只同步清单管理范围内的指定相对路径，可重复传入")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="输出格式")
    args = parser.parse_args()

    if args.only and args.path:
        parser.error("--only and --path cannot be used together")

    private_root = Path(args.private_root).expanduser().resolve()
    if not private_root.exists():
        raise SystemExit(f"私有 vault 不存在: {private_root}")

    manifest = load_manifest()
    categories = manifest.get("categories", {}) if isinstance(manifest.get("categories"), dict) else {}
    ignore_globs = [str(item) for item in manifest.get("ignore_globs", []) if str(item).strip()]
    protected_globs = [str(item) for item in manifest.get("protected_globs", []) if str(item).strip()]
    selected_categories = args.only or list(categories.keys())

    all_managed_roots: list[Path] = []
    for rel_paths in categories.values():
        if not isinstance(rel_paths, list):
            continue
        for rel in rel_paths:
            try:
                all_managed_roots.append(normalized_relative_path(str(rel)))
            except ValueError:
                continue

    selected_paths: list[Path] = []
    if args.path:
        for raw_path in args.path:
            try:
                rel_path = normalized_relative_path(raw_path)
            except ValueError as exc:
                raise SystemExit(str(exc)) from exc
            if should_ignore(rel_path, protected_globs):
                raise SystemExit(f"protected path: {rel_path.as_posix()}")
            if not is_managed_path(rel_path, all_managed_roots):
                raise SystemExit(f"path is outside managed scaffold: {rel_path.as_posix()}")
            selected_paths.append(rel_path)
    else:
        for category in selected_categories:
            rel_paths = categories.get(category, [])
            if not isinstance(rel_paths, list):
                continue
            for rel in rel_paths:
                try:
                    selected_paths.append(normalized_relative_path(str(rel)))
                except ValueError as exc:
                    raise SystemExit(str(exc)) from exc

    actions: list[dict[str, str]] = []
    seen: set[str] = set()
    for rel_path in selected_paths:
        rel_key = rel_path.as_posix()
        if rel_key in seen:
            continue
        seen.add(rel_key)
        if should_ignore(rel_path, protected_globs):
            continue
        src = VAULT_ROOT / rel_path
        dst = private_root / rel_path
        if not src.exists():
            continue
        if src.is_file():
            if not should_ignore(rel_path, ignore_globs):
                actions.append(copy_file(src, dst, rel_path=rel_key, dry_run=args.dry_run))
        else:
            actions.extend(
                sync_tree(
                    src,
                    dst,
                    dry_run=args.dry_run,
                    ignore_globs=ignore_globs,
                    protected_globs=protected_globs,
                )
            )

    payload = {
        "private_root": str(private_root),
        "dry_run": args.dry_run,
        "categories": [] if args.path else selected_categories,
        "requested_paths": args.path or [],
        "summary": summary_for(actions),
        "actions": actions,
    }
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    print(f"private_root={private_root}")
    print(f"categories={','.join(selected_categories) if not args.path else '-'}")
    for action in actions:
        print(f"{action['action']}: {action['path']}")
    summary = payload["summary"]
    print(f"created={summary['created']} updated={summary['updated']} skipped={summary['skipped']}")


if __name__ == "__main__":
    main()
