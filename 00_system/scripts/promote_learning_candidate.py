from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from wiki_lib import (
    SCRIPT_DIR,
    VAULT_ROOT,
    append_log,
    load_page,
    render_markdown,
    slugify,
    today_iso,
    update_page_frontmatter,
    write_text,
)


TARGET_MAP = {
    "模式": ("30_shared/patterns", "共享"),
    "提示词": ("30_shared/prompts", "共享"),
    "工具": ("30_shared/tools", "共享"),
    "架构": ("30_shared/architectures", "共享"),
    "分析": ("40_outputs/analyses", "输出"),
}


def section_text(body: str, heading: str) -> str:
    marker = f"## {heading}"
    if marker not in body:
        return ""
    start = body.index(marker) + len(marker)
    next_pos = body.find("\n## ", start)
    block = body[start: next_pos if next_pos != -1 else len(body)].strip()
    return block


def build_promoted_content(
    *,
    title: str,
    note_type: str,
    domain: str,
    project: str,
    tags: list[str],
    summary: str,
    reflection_link: str,
    observation: str,
    improvement: str,
    validation: str,
) -> str:
    frontmatter = {
        "title": title,
        "type": note_type,
        "domain": domain,
        "project": project,
        "status": "常用" if domain == "共享" else "活跃",
        "tags": tags,
        "updated": today_iso(),
        "summary": summary,
    }
    body = "\n".join(
        [
            f"# {title}",
            "",
            "## 摘要",
            "",
            summary,
            "",
            "## 来源候选",
            "",
            f"- {reflection_link}",
            "",
            "## 观察",
            "",
            observation or "- ",
            "",
            "## 建议做法",
            "",
            improvement or "- ",
            "",
            "## 后续验证",
            "",
            validation or "- ",
        ]
    )
    return render_markdown(frontmatter, body)


def main() -> None:
    parser = argparse.ArgumentParser(description="把学习候选提升为共享页或正式分析页。")
    parser.add_argument("--source", required=True, help="候选反思页路径")
    parser.add_argument("--target-type", required=True, choices=sorted(TARGET_MAP), help="提升目标类型")
    parser.add_argument("--title", default="", help="目标页标题，默认沿用候选标题")
    args = parser.parse_args()

    source_path = Path(args.source).expanduser().resolve()
    if not source_path.exists():
        raise SystemExit(f"候选页不存在: {source_path}")

    page = load_page(source_path)
    frontmatter = page["frontmatter"]
    if not isinstance(frontmatter, dict):
        raise SystemExit("候选页缺少 frontmatter。")
    if str(frontmatter.get("type") or "").strip() != "反思":
        raise SystemExit("只支持从 `反思` 类型页面提升。")

    title = args.title.strip() or str(frontmatter.get("title") or source_path.stem)
    note_type = args.target_type
    target_folder, domain = TARGET_MAP[note_type]
    project = str(frontmatter.get("project") or "").strip()
    tags = [str(tag) for tag in page["tags"]]
    summary = str(frontmatter.get("summary") or f"{title} 的升级结果。").strip()
    observation = section_text(str(page["body"]), "观察")
    improvement = section_text(str(page["body"]), "候选改进")
    validation = section_text(str(page["body"]), "后续验证")
    reflection_link = f"[[{Path(str(page['rel_path'])).with_suffix('').as_posix()}|{title} 候选]]"

    destination = VAULT_ROOT / target_folder / f"{slugify(title)}.md"
    content = build_promoted_content(
        title=title,
        note_type=note_type,
        domain=domain,
        project="" if domain == "共享" else project,
        tags=tags,
        summary=summary,
        reflection_link=reflection_link,
        observation=observation,
        improvement=improvement,
        validation=validation,
    )
    write_text(destination, content)
    update_page_frontmatter(source_path, {"status": "已提升", "promoted_to": destination.relative_to(VAULT_ROOT).as_posix(), "updated": today_iso()})
    append_log("更新", title, f"已将学习候选提升到 {destination.relative_to(VAULT_ROOT).as_posix()}")
    subprocess.run([sys.executable, str(SCRIPT_DIR / "rebuild_indexes.py")], check=True)
    print(destination)


if __name__ == "__main__":
    main()
