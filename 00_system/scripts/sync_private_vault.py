from __future__ import annotations

import argparse
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
            "Home.md",
            "README.md",
            "README-zh.md",
            "index.md",
            "使用手册.md",
            "会话启动页.md",
        ],
        "system": ["00_system"],
        "docs": ["docs"],
        "prompts": ["30_shared/prompts"],
    },
    "ignore_globs": ["**/__pycache__/**", "**/*.pyc"],
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


def copy_file(src: Path, dst: Path, *, dry_run: bool) -> str:
    action = "update" if dst.exists() else "create"
    if not dry_run:
        ensure_parent(dst)
        shutil.copy2(src, dst)
    return f"{action}: {dst}"


def sync_tree(src_root: Path, dst_root: Path, *, dry_run: bool, ignore_globs: list[str]) -> list[str]:
    actions: list[str] = []
    if not src_root.exists():
        return actions
    for src in src_root.rglob("*"):
        if src.is_dir():
            continue
        if should_ignore(src, ignore_globs):
            continue
        rel = src.relative_to(src_root)
        dst = dst_root / rel
        actions.append(copy_file(src, dst, dry_run=dry_run))
    return actions


def main() -> None:
    parser = argparse.ArgumentParser(description="把公开脚手架的系统层同步到私有 vault。")
    parser.add_argument("--private-root", default=str(default_private_root()), help="私有 vault 根目录")
    parser.add_argument("--dry-run", action="store_true", help="只显示将要同步的内容，不实际写入")
    parser.add_argument("--only", action="append", choices=["root", "system", "docs", "prompts"], help="只同步指定类别，可重复传入")
    args = parser.parse_args()

    private_root = Path(args.private_root).expanduser().resolve()
    if not private_root.exists():
        raise SystemExit(f"私有 vault 不存在: {private_root}")

    manifest = load_manifest()
    categories = manifest.get("categories", {}) if isinstance(manifest.get("categories"), dict) else {}
    ignore_globs = [str(item) for item in manifest.get("ignore_globs", []) if str(item).strip()]
    selected_categories = args.only or list(categories.keys())

    actions: list[str] = []
    for category in selected_categories:
        rel_paths = categories.get(category, [])
        if not isinstance(rel_paths, list):
            continue
        for rel in rel_paths:
            src = VAULT_ROOT / str(rel)
            dst = private_root / str(rel)
            if not src.exists():
                continue
            if src.is_file():
                actions.append(copy_file(src, dst, dry_run=args.dry_run))
            else:
                actions.extend(sync_tree(src, dst, dry_run=args.dry_run, ignore_globs=ignore_globs))

    print(f"private_root={private_root}")
    print(f"categories={','.join(selected_categories)}")
    for action in actions:
        print(action)
    print(f"count={len(actions)}")


if __name__ == "__main__":
    main()
