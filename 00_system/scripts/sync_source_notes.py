from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

from wiki_lib import (
    SCRIPT_DIR,
    VAULT_ROOT,
    append_log,
    iter_markdown_files,
    load_page,
    parse_date,
    update_page_frontmatter,
)

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)")


def resolve_link(target: str, page_map: dict[str, Path], stem_map: dict[str, list[Path]]) -> Path | None:
    normalized = target.strip().replace("\\", "/").removesuffix(".md")
    if normalized in page_map:
        return page_map[normalized]
    stem = Path(normalized).name
    matches = stem_map.get(stem, [])
    if len(matches) == 1:
        return matches[0]
    return None


def compute_status(derived_pages: list[str], current_status: str) -> str:
    if any(path.startswith("30_shared/") or path.startswith("10_personal/") for path in derived_pages):
        return "已提升"
    if derived_pages:
        return "已沉淀"
    if current_status in {"已归档", "已提升", "已沉淀"}:
        return current_status
    if current_status == "已总结":
        return current_status
    return current_status or "已登记"


def build_backlinks() -> tuple[list[dict[str, object]], dict[Path, set[Path]]]:
    pages = [load_page(path) for path in iter_markdown_files()]
    page_map = {str(page["rel_path"]).removesuffix(".md"): page["path"] for page in pages}
    stem_map: dict[str, list[Path]] = defaultdict(list)
    incoming: dict[Path, set[Path]] = defaultdict(set)

    for rel_path, path in page_map.items():
        stem_map[Path(rel_path).name].append(path)

    for page in pages:
        for match in WIKILINK_RE.findall(str(page["body"])):
            resolved = resolve_link(match, page_map, stem_map)
            if resolved is not None:
                incoming[resolved].add(page["path"])
    return pages, incoming


def main() -> None:
    parser = argparse.ArgumentParser(description="根据反向链接同步来源笔记的 derived_pages 与 ingest_status。")
    parser.add_argument("--rebuild", action="store_true", help="同步后重建索引")
    args = parser.parse_args()

    pages, incoming = build_backlinks()
    updates = 0

    page_by_path = {Path(str(page["path"])).resolve(): page for page in pages}
    for page in pages:
        frontmatter = page["frontmatter"]
        if not isinstance(frontmatter, dict):
            continue
        note_type = str(frontmatter.get("type") or "").strip()
        if note_type != "来源":
            continue

        backlinks = []
        for backlink in sorted(incoming.get(page["path"], set())):
            rel_path = backlink.relative_to(VAULT_ROOT).as_posix()
            if rel_path.endswith("来源.md"):
                continue
            meta = page_by_path.get(backlink.resolve())
            if meta and isinstance(meta["frontmatter"], dict):
                backlink_type = str(meta["frontmatter"].get("type") or "").strip()
                if backlink_type == "来源":
                    continue
            backlinks.append(rel_path)

        existing_derived = frontmatter.get("derived_pages")
        existing_derived_list = [str(item) for item in existing_derived] if isinstance(existing_derived, list) else []
        current_status = str(frontmatter.get("ingest_status") or "").strip()
        next_status = compute_status(backlinks, current_status)

        updates_needed = False
        payload: dict[str, object] = {}
        if existing_derived_list != backlinks:
            payload["derived_pages"] = backlinks
            updates_needed = True
        if current_status != next_status:
            payload["ingest_status"] = next_status
            updates_needed = True

        review_due = str(frontmatter.get("review_due") or "").strip()
        if not review_due and parse_date(str(frontmatter.get("updated") or "")) is not None:
            payload["review_due"] = str(frontmatter.get("updated"))
            updates_needed = True

        if updates_needed:
            update_page_frontmatter(Path(str(page["path"])), payload)
            updates += 1

    if updates:
        append_log("更新", "同步来源状态", f"已更新 {updates} 个来源笔记的 derived_pages / ingest_status")

    if args.rebuild:
        subprocess.run([sys.executable, str(SCRIPT_DIR / "rebuild_indexes.py")], check=True)

    print(f"updated={updates}")


if __name__ == "__main__":
    main()
