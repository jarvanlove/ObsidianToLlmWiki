from __future__ import annotations

import argparse
import subprocess
import sys

from wiki_lib import SCRIPT_DIR, append_log, iter_markdown_files, load_page, now_iso, update_page_frontmatter


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


def matches(
    page: dict[str, object],
    *,
    risk_level: str,
    upgrade_mode: str,
    candidate_domain: str,
    min_score: int | None,
    status_filter: str,
) -> bool:
    frontmatter = page["frontmatter"]
    if not isinstance(frontmatter, dict):
        return False
    if risk_level and str(frontmatter.get("candidate_risk_level") or "").strip() != risk_level:
        return False
    if upgrade_mode and str(frontmatter.get("candidate_upgrade_mode") or "").strip() != upgrade_mode:
        return False
    if candidate_domain and str(frontmatter.get("candidate_domain") or "").strip() != candidate_domain:
        return False
    if status_filter and str(frontmatter.get("status") or "").strip() != status_filter:
        return False
    if min_score is not None:
        try:
            score = int(frontmatter.get("candidate_score") or 0)
        except (TypeError, ValueError):
            score = 0
        if score < min_score:
            return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="对学习候选做批量审核。")
    parser.add_argument("--action", required=True, choices=["approve", "archive", "reopen"], help="批量审核动作")
    parser.add_argument("--risk-level", default="", choices=["", "low", "medium", "high"], help="按风险等级过滤")
    parser.add_argument("--upgrade-mode", default="", choices=["", "auto", "semi_auto", "manual"], help="按升级模式过滤")
    parser.add_argument("--candidate-domain", default="", help="按候选领域过滤，例如 retrieval / governance")
    parser.add_argument("--min-score", type=int, default=None, help="只处理不低于该分数的候选")
    parser.add_argument("--status", default="候选", help="只处理指定状态的候选，默认处理候选态")
    parser.add_argument("--max-count", type=int, default=0, help="最多处理多少条，0 表示不限")
    parser.add_argument("--review-note", default="", help="审核备注")
    parser.add_argument("--rebuild", action="store_true", help="处理后重建索引")
    args = parser.parse_args()

    updated = 0
    for page in reflection_pages():
        if not matches(
            page,
            risk_level=args.risk_level,
            upgrade_mode=args.upgrade_mode,
            candidate_domain=args.candidate_domain.strip(),
            min_score=args.min_score,
            status_filter=args.status.strip(),
        ):
            continue

        if args.max_count and updated >= args.max_count:
            break

        if args.action == "approve":
            payload = {"status": "已批准", "approved_at": now_iso(), "review_note": args.review_note}
        elif args.action == "archive":
            payload = {"status": "已归档", "review_note": args.review_note}
        else:
            payload = {"status": "候选", "approved_at": "", "review_note": args.review_note}

        update_page_frontmatter(page["path"], payload)
        updated += 1

    if updated:
        append_log(
            "更新",
            "批量审核学习候选",
            f"action={args.action}; updated={updated}; risk={args.risk_level or 'all'}; "
            f"mode={args.upgrade_mode or 'all'}; domain={args.candidate_domain.strip() or 'all'}",
        )

    if args.rebuild and updated:
        subprocess.run([sys.executable, str(SCRIPT_DIR / "rebuild_indexes.py")], check=True)

    print(f"updated={updated}")


if __name__ == "__main__":
    main()
