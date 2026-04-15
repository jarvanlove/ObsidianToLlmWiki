from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

from wiki_lib import SCRIPT_DIR, VAULT_ROOT, append_log, iter_markdown_files, load_page, parse_date, write_text

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


def should_skip_orphan(rel_path: str) -> bool:
    return (
        rel_path in {"Home.md", "index.md", "log.md", "AGENTS.md", "CLAUDE.md", "README.md"}
        or rel_path.endswith("/索引.md")
        or rel_path.startswith("40_outputs/analyses/知识库体检-")
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="执行基础知识库体检，检查孤儿页与过期页。")
    parser.add_argument("--stale-days", type=int, default=45, help="超过多少天未更新则视为过期")
    args = parser.parse_args()

    subprocess.run([sys.executable, str(SCRIPT_DIR / "rebuild_indexes.py")], check=True)

    pages = [load_page(path) for path in iter_markdown_files()]
    page_map = {str(page["rel_path"]).removesuffix(".md"): page["path"] for page in pages}
    stem_map: dict[str, list[Path]] = defaultdict(list)
    incoming: dict[Path, set[Path]] = defaultdict(set)

    for rel_path, path in page_map.items():
        stem_map[Path(rel_path).name].append(path)

    for page in pages:
        matches = WIKILINK_RE.findall(str(page["body"]))
        for match in matches:
            resolved = resolve_link(match, page_map, stem_map)
            if resolved is not None:
                incoming[resolved].add(page["path"])

    today = date.today()
    orphans: list[dict[str, object]] = []
    stale: list[dict[str, object]] = []

    for page in pages:
        rel_path = str(page["rel_path"])
        if should_skip_orphan(rel_path):
            continue
        if page["path"] not in incoming:
            orphans.append(page)

        frontmatter = page["frontmatter"]
        if isinstance(frontmatter, dict):
            updated = parse_date(str(frontmatter.get("updated") or ""))
            if updated is not None and (today - updated).days > args.stale_days:
                stale.append(page)

    report_path = VAULT_ROOT / "40_outputs" / "analyses" / f"知识库体检-{today.isoformat()}.md"
    lines = [
        f"# 知识库体检 {today.isoformat()}",
        "",
        f"- 孤儿页面: {len(orphans)}",
        f"- 过期页面: {len(stale)}",
        "",
        "## 孤儿页面",
        "",
    ]
    if orphans:
        for page in sorted(orphans, key=lambda item: str(item["rel_path"])):
            lines.append(f"- [[{Path(str(page['rel_path'])).with_suffix('').as_posix()}|{page['title']}]]")
    else:
        lines.append("- 无。")

    lines.extend(["", "## 过期页面", ""])
    if stale:
        for page in sorted(stale, key=lambda item: str(item["rel_path"])):
            lines.append(f"- [[{Path(str(page['rel_path'])).with_suffix('').as_posix()}|{page['title']}]]")
    else:
        lines.append("- 无。")

    write_text(report_path, "\n".join(lines))
    append_log("体检", "知识库体检", f"报告已写入 {report_path.relative_to(VAULT_ROOT).as_posix()}")
    print(report_path)


if __name__ == "__main__":
    main()
