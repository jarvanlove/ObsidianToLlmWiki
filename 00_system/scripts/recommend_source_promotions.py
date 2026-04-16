from __future__ import annotations

import argparse
import subprocess
import sys
from collections import Counter
from pathlib import Path

from wiki_lib import SCRIPT_DIR, VAULT_ROOT, append_log, iter_markdown_files, load_page, update_page_frontmatter


def load_pages() -> list[dict[str, object]]:
    return [load_page(path) for path in iter_markdown_files()]


def shared_tag_map(pages: list[dict[str, object]]) -> set[str]:
    tags: set[str] = set()
    for page in pages:
        rel_path = str(page["rel_path"])
        frontmatter = page["frontmatter"]
        if not isinstance(frontmatter, dict):
            continue
        note_type = str(frontmatter.get("type") or "").strip()
        if rel_path.startswith("30_shared/") and note_type in {"模式", "提示词", "工具", "架构"}:
            tags.update(str(tag).strip().lower() for tag in page["tags"] if str(tag).strip())
    return tags


def source_recommendations(page: dict[str, object], *, shared_tags: set[str], project_tag_counts: Counter[str]) -> list[str]:
    frontmatter = page["frontmatter"]
    if not isinstance(frontmatter, dict):
        return []
    project_slug = str(frontmatter.get("project") or "").strip()
    recommendations: list[str] = []
    tags = [str(tag).strip().lower() for tag in page["tags"] if str(tag).strip()]

    for tag in tags:
        if tag in shared_tags:
            recommendations.append(f"link-shared:{tag}")
        elif project_tag_counts[tag] >= 2:
            recommendations.append(f"promote-shared:{tag}")

    derived_pages = frontmatter.get("derived_pages")
    derived_list = [str(item) for item in derived_pages] if isinstance(derived_pages, list) else []
    if not derived_list and project_slug:
        recommendations.append(f"file-project:{project_slug}")
    if derived_list and not any(path.startswith("30_shared/") for path in derived_list):
        overlap_tags = [tag for tag in tags if tag not in shared_tags and project_tag_counts[tag] >= 2]
        if overlap_tags:
            recommendations.append(f"promote-pattern:{overlap_tags[0]}")

    return sorted(dict.fromkeys(recommendations))


def main() -> None:
    parser = argparse.ArgumentParser(description="为来源笔记回填推荐的沉淀目标。")
    parser.add_argument("--rebuild", action="store_true", help="更新后重建索引")
    args = parser.parse_args()

    pages = load_pages()
    shared_tags = shared_tag_map(pages)
    project_tag_counts: Counter[str] = Counter()
    for page in pages:
        rel_path = str(page["rel_path"])
        frontmatter = page["frontmatter"]
        if not isinstance(frontmatter, dict):
            continue
        if not rel_path.startswith("20_projects/active/"):
            continue
        for tag in page["tags"]:
            normalized = str(tag).strip().lower()
            if normalized:
                project_tag_counts[normalized] += 1

    updates = 0
    for page in pages:
        frontmatter = page["frontmatter"]
        if not isinstance(frontmatter, dict):
            continue
        if str(frontmatter.get("type") or "").strip() != "来源":
            continue

        recommended = source_recommendations(page, shared_tags=shared_tags, project_tag_counts=project_tag_counts)
        current = frontmatter.get("recommended_targets")
        current_list = [str(item) for item in current] if isinstance(current, list) else []
        if current_list != recommended:
            update_page_frontmatter(Path(str(page["path"])), {"recommended_targets": recommended})
            updates += 1

    if updates:
        append_log("更新", "推荐来源提升目标", f"已更新 {updates} 个来源笔记的 recommended_targets")

    if args.rebuild:
        subprocess.run([sys.executable, str(SCRIPT_DIR / "rebuild_indexes.py")], check=True)

    print(f"updated={updates}")


if __name__ == "__main__":
    main()
