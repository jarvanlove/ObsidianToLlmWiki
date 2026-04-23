from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import date

from wiki_lib import SCRIPT_DIR, VAULT_ROOT, append_log, iter_markdown_files, load_page, parse_date, update_page_frontmatter


def reflection_pages() -> list[dict[str, object]]:
    pages: list[dict[str, object]] = []
    for path in iter_markdown_files():
        page = load_page(path)
        frontmatter = page["frontmatter"]
        if not isinstance(frontmatter, dict):
            continue
        rel_path = str(page["rel_path"])
        note_type = str(frontmatter.get("type") or "").strip()
        if rel_path.startswith("40_outputs/reflections/") and note_type == "反思":
            pages.append(page)
    return pages


def should_archive(page: dict[str, object], *, stale_days: int, min_score: int) -> bool:
    frontmatter = page["frontmatter"]
    if not isinstance(frontmatter, dict):
        return False
    status = str(frontmatter.get("status") or "").strip()
    if status in {"已提升", "已归档"}:
        return False
    promoted_to = str(frontmatter.get("promoted_to") or "").strip()
    if promoted_to:
        return False
    try:
        score = int(frontmatter.get("candidate_score") or 0)
    except (TypeError, ValueError):
        score = 0
    freshness = parse_date(str(frontmatter.get("candidate_freshness") or "")) or parse_date(str(frontmatter.get("updated") or ""))
    if freshness is None:
        return score < min_score
    age_days = (date.today() - freshness).days
    return score < min_score and age_days > stale_days


def main() -> None:
    parser = argparse.ArgumentParser(description="清理低分且过期的学习候选。")
    parser.add_argument("--stale-days", type=int, default=14, help="超过多少天的低分候选会被归档")
    parser.add_argument("--min-score", type=int, default=4, help="低于该分数的候选会被视为低分")
    parser.add_argument("--rebuild", action="store_true", help="归档后重建索引")
    args = parser.parse_args()

    archived = 0
    for page in reflection_pages():
        if should_archive(page, stale_days=args.stale_days, min_score=args.min_score):
            update_page_frontmatter(page["path"], {"status": "已归档"})
            archived += 1

    if archived:
        append_log("更新", "整理学习候选", f"已归档 {archived} 个低分且过期的学习候选")

    if args.rebuild and archived:
        subprocess.run([sys.executable, str(SCRIPT_DIR / "rebuild_indexes.py")], check=True)

    print(f"archived={archived}")


if __name__ == "__main__":
    main()
