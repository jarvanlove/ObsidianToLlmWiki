from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import date
from pathlib import Path

from schema_lib import page_link
from wiki_lib import SCRIPT_DIR, VAULT_ROOT, append_log, iter_markdown_files, load_page, write_text


def list_items(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def section_text(body: str, heading: str) -> str:
    marker = f"## {heading}"
    if marker not in body:
        return ""
    start = body.index(marker) + len(marker)
    next_pos = body.find("\n## ", start)
    return body[start: next_pos if next_pos != -1 else len(body)].strip()


def target_label(target: str) -> str:
    if target.startswith("file-project:"):
        return "项目层"
    labels = {
        "review-personal": "个人层",
        "review-shared": "共享层",
        "review-output": "输出层",
    }
    return labels.get(target, target)


def target_reason(target: str) -> str:
    if target.startswith("file-project:"):
        return "章节来自项目资料，优先判断是否应更新项目事实、架构、决策、风险或任务。"
    reasons = {
        "review-personal": "可能沉淀为个人长期认知、学习笔记、偏好或方法。",
        "review-shared": "可能沉淀为跨项目可复用的方法、模式、提示词或架构经验。",
        "review-output": "可能沉淀为一次性分析、课程材料、复盘或阶段报告。",
    }
    return reasons.get(target, "需要人工判断沉淀目标。")


def next_action(target: str) -> str:
    if target.startswith("file-project:"):
        return "阅读章节笔记与文档地图，更新对应项目页，并在正式页回链本章节。"
    if target == "review-shared":
        return "判断是否跨项目复用；若成立，创建或更新 `30_shared/` 正式知识页。"
    if target == "review-personal":
        return "判断是否属于个人长期认知；若成立，创建或更新 `10_personal/` 页面。"
    if target == "review-output":
        return "判断是否是一份阶段性输出；若成立，创建或更新 `40_outputs/` 分析页。"
    return "人工复核目标层，并创建或更新正式知识页。"


def section_pages(project: str) -> list[dict[str, object]]:
    pages: list[dict[str, object]] = []
    for path in iter_markdown_files():
        page = load_page(path)
        frontmatter = page["frontmatter"]
        if not isinstance(frontmatter, dict):
            continue
        if str(frontmatter.get("type") or "").strip() != "章节笔记":
            continue
        if project and str(frontmatter.get("project") or "").strip() != project:
            continue
        status = str(frontmatter.get("status") or "").strip()
        if status in {"已沉淀", "已提升", "已归档"}:
            continue
        if not list_items(frontmatter.get("recommended_targets")):
            continue
        pages.append(page)
    return sorted(pages, key=lambda item: str(item["rel_path"]))


def render_candidate(page: dict[str, object], index: int) -> list[str]:
    frontmatter = page["frontmatter"]
    assert isinstance(frontmatter, dict)
    rel_path = str(page["rel_path"])
    title = str(page["title"])
    body = str(page["body"])
    source_refs = list_items(frontmatter.get("source_refs"))
    targets = list_items(frontmatter.get("recommended_targets"))
    source_note = str(frontmatter.get("source_note") or "").strip()
    document_map = str(frontmatter.get("document_map") or "").strip()
    theme = section_text(body, "本节主题") or "- 待人工复核。"
    facts = section_text(body, "关键事实") or "- 待人工复核。"

    lines = [
        f"### {index}. {page_link(rel_path, title)}",
        "",
        f"- 来源章节: {page_link(rel_path, title)}",
        f"- 来源引用: {', '.join(f'`{ref}`' for ref in source_refs) if source_refs else '待补充'}",
        f"- 来源笔记: `{source_note or '待补充'}`",
        f"- 文档地图: `{document_map or '待补充'}`",
        f"- 推荐目标: {', '.join(f'`{target}`' for target in targets)}",
        "",
        "#### 推荐理由",
        "",
    ]
    for target in targets:
        lines.append(f"- {target_label(target)}：{target_reason(target)}")

    lines.extend(["", "#### 章节主题", "", theme, "", "#### 关键事实", "", facts, "", "#### 下一步动作", ""])
    for target in targets:
        lines.append(f"- {target_label(target)}：{next_action(target)}")
    return lines


def build_report(pages: list[dict[str, object]], project: str) -> str:
    today = date.today().isoformat()
    title_suffix = f" - {project}" if project else ""
    lines = [
        "---",
        f"title: 资料沉淀候选 {today}{title_suffix}",
        "type: 分析",
        "domain: 输出",
        "project: ",
        "status: 候选",
        "tags: [source, ingest, promotion]",
        f"updated: {today}",
        f"summary: 从章节笔记生成的待沉淀候选清单，共 {len(pages)} 条。",
        "---",
        "",
        f"# 资料沉淀候选 {today}{title_suffix}",
        "",
        "## 说明",
        "",
        "- 本报告只列候选，不自动创建正式知识页。",
        "- 每个候选必须回到来源章节、source_refs 和文档地图核对后再沉淀。",
        "- 正式知识页应回链来源章节，避免结论失去出处。",
        "",
        "## 候选列表",
        "",
    ]
    if not pages:
        lines.append("- 无待沉淀章节笔记。")
        return "\n".join(lines) + "\n"

    for index, page in enumerate(pages, start=1):
        lines.extend(render_candidate(page, index))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="从章节笔记生成资料沉淀候选清单。")
    parser.add_argument("--project", default="", help="只扫描指定 project slug")
    parser.add_argument("--output", default="", help="输出文件，默认写入 40_outputs/analyses")
    parser.add_argument("--rebuild", action="store_true", help="生成后重建索引")
    args = parser.parse_args()

    pages = section_pages(args.project.strip())
    today = date.today().isoformat()
    if args.output.strip():
        output_path = Path(args.output).expanduser().resolve()
    else:
        suffix = f"-{args.project.strip()}" if args.project.strip() else ""
        output_path = VAULT_ROOT / "40_outputs" / "analyses" / f"资料沉淀候选-{today}{suffix}.md"

    write_text(output_path, build_report(pages, args.project.strip()))
    append_log("分析", "资料沉淀候选", f"已生成 {output_path.relative_to(VAULT_ROOT).as_posix()}，候选数 {len(pages)}")
    if args.rebuild:
        subprocess.run([sys.executable, str(SCRIPT_DIR / "rebuild_indexes.py")], check=True)
    print(output_path)


if __name__ == "__main__":
    main()
