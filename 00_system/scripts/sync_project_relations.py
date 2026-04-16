from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

from wiki_lib import SCRIPT_DIR, VAULT_ROOT, append_log, iter_markdown_files, load_page, update_page_frontmatter

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:\|[^\]]+)?\]\]")
SECTION_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)
SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？.!?])")


SECTION_FIELD_MAP = {
    "依赖项目": "depends_on",
    "复用资产": "reuses",
    "输出资产": "produces",
    "相关项目": "related_to",
}
PROJECT_CONTEXT_FILES = ["关系.md", "架构.md", "决策.md", "project.memory.md"]
DEPENDENCY_HEADINGS = {"依赖项目", "关键依赖", "依赖", "上游依赖"}
REUSE_HEADINGS = {"复用资产", "复用", "共享资产", "共享模式", "组件", "关联页面"}
PRODUCE_HEADINGS = {"输出资产", "输出", "产出"}
RELATED_HEADINGS = {"相关项目", "关联项目", "关联页面"}
DEPENDENCY_HINTS = {"依赖", "上游", "阻塞", "前置", "调用", "接入", "需要"}
REUSE_HINTS = {"复用", "沿用", "参考", "共享", "组件", "能力", "采用"}
PRODUCE_HINTS = {"输出", "产出", "沉淀", "生成", "提供", "暴露"}
RELATED_HINTS = {"相关", "关联", "协同", "配合", "对齐"}


def split_sections(body: str) -> dict[str, str]:
    matches = list(SECTION_RE.finditer(body))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        heading = match.group(1).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        sections[heading] = body[start:end].strip()
    return sections


def extract_wikilinks(text: str) -> list[str]:
    return [match.strip() for match in WIKILINK_RE.findall(text)]


def normalize_target(target: str) -> str:
    cleaned = target.strip().replace("\\", "/").removesuffix(".md")
    return cleaned


def to_slug(target: str) -> str:
    normalized = normalize_target(target)
    return Path(normalized).name


def sentence_for_target(text: str, target: str) -> str:
    sentences = SENTENCE_SPLIT_RE.split(text)
    for sentence in sentences:
        if target in sentence:
            return sentence
    return text


def infer_relation_from_sentence(sentence: str) -> str:
    sentence_text = sentence.strip()
    if any(keyword in sentence_text for keyword in DEPENDENCY_HINTS):
        return "depends_on"
    if any(keyword in sentence_text for keyword in REUSE_HINTS):
        return "reuses"
    if any(keyword in sentence_text for keyword in PRODUCE_HINTS):
        return "produces"
    if any(keyword in sentence_text for keyword in RELATED_HINTS):
        return "related_to"
    return "related_to"


def classify_targets(
    *,
    text: str,
    heading: str,
    current_project: str,
    all_project_slugs: set[str],
    depends_on: set[str],
    reuses: set[str],
    produces: set[str],
    related_to: set[str],
) -> None:
    heading_text = heading.strip()
    for target in extract_wikilinks(text):
        normalized = normalize_target(target)
        sentence = sentence_for_target(text, target)
        inferred_relation = infer_relation_from_sentence(sentence)
        if normalized.startswith("20_projects/active/"):
            slug = to_slug(normalized)
            if not slug or slug == current_project or slug not in all_project_slugs:
                continue
            if heading_text in DEPENDENCY_HEADINGS:
                depends_on.add(slug)
            elif heading_text in RELATED_HEADINGS or heading_text in REUSE_HEADINGS or heading_text in PRODUCE_HEADINGS:
                related_to.add(slug)
            elif inferred_relation == "depends_on":
                depends_on.add(slug)
            else:
                related_to.add(slug)
        elif normalized.startswith("30_shared/"):
            if heading_text in PRODUCE_HEADINGS:
                produces.add(normalized)
            elif heading_text in REUSE_HEADINGS:
                reuses.add(normalized)
            elif inferred_relation == "produces":
                produces.add(normalized)
            else:
                reuses.add(normalized)


def sync_one_project(index_page: dict[str, object], relation_page: dict[str, object] | None, all_project_slugs: set[str]) -> bool:
    frontmatter = index_page["frontmatter"]
    if not isinstance(frontmatter, dict):
        return False

    updates: dict[str, object] = {}
    current_project = str(frontmatter.get("project") or "").strip()
    depends_on: set[str] = set()
    reuses: set[str] = set()
    produces: set[str] = set()
    related_to: set[str] = set()

    project_root = Path(str(index_page["path"])).parent
    for file_name in PROJECT_CONTEXT_FILES:
        page_path = project_root / file_name
        if not page_path.exists():
            continue
        page = load_page(page_path)
        body = str(page["body"])
        sections = split_sections(body)
        if sections:
            for heading, text in sections.items():
                classify_targets(
                    text=text,
                    heading=heading,
                    current_project=current_project,
                    all_project_slugs=all_project_slugs,
                    depends_on=depends_on,
                    reuses=reuses,
                    produces=produces,
                    related_to=related_to,
                )
        else:
            classify_targets(
                text=body,
                heading="",
                current_project=current_project,
                all_project_slugs=all_project_slugs,
                depends_on=depends_on,
                reuses=reuses,
                produces=produces,
                related_to=related_to,
            )

    final_depends = sorted(depends_on)
    final_reuses = sorted(reuses)
    final_produces = sorted(produces)
    final_related = sorted(related_to)

    next_values = {
        "depends_on": final_depends,
        "reuses": final_reuses,
        "produces": final_produces,
        "related_to": final_related,
    }
    changed = False
    for field_name, next_value in next_values.items():
        current = frontmatter.get(field_name)
        current_value = [str(item) for item in current] if isinstance(current, list) else []
        if current_value != next_value:
            updates[field_name] = next_value
            changed = True

    if changed:
        update_page_frontmatter(Path(str(index_page["path"])), updates)
    return changed


def main() -> None:
    parser = argparse.ArgumentParser(description="把项目关系页同步回项目索引 frontmatter。")
    parser.add_argument("--rebuild", action="store_true", help="同步后重建索引")
    args = parser.parse_args()

    pages = [load_page(path) for path in iter_markdown_files()]
    project_indexes = {
        str(page["path"].parent): page
        for page in pages
        if str(page["rel_path"]).startswith("20_projects/active/") and str(page["rel_path"]).endswith("/索引.md")
    }
    relation_pages = {
        str(page["path"].parent): page
        for page in pages
        if str(page["rel_path"]).startswith("20_projects/active/") and str(page["rel_path"]).endswith("/关系.md")
    }
    project_slugs = {str(page["frontmatter"].get("project") or "").strip() for page in project_indexes.values() if isinstance(page["frontmatter"], dict)}

    updates = 0
    for root_key, index_page in project_indexes.items():
        relation_page = relation_pages.get(root_key)
        if sync_one_project(index_page, relation_page, project_slugs):
            updates += 1

    if updates:
        append_log("更新", "同步项目关系", f"已更新 {updates} 个项目索引的关系字段")

    if args.rebuild:
        subprocess.run([sys.executable, str(SCRIPT_DIR / "rebuild_indexes.py")], check=True)

    print(f"updated={updates}")


if __name__ == "__main__":
    main()
