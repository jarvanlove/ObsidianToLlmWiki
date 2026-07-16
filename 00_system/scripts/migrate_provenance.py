from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from wiki_lib import VAULT_ROOT, iter_markdown_files, load_page, today_iso, update_page_frontmatter


KNOWLEDGE_TYPES = {"概念", "实体", "综述", "模式", "工具", "架构", "分析", "简报", "项目经验"}
SOURCE_HEADING_RE = re.compile(r"^#{1,6}\s*(来源|出处|参考|references?|sources?)\b", re.IGNORECASE)
WIKI_LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
SOURCE_LINE_RE = re.compile(
    r"^\s*(?:>\s*)?(?:[-*]\s*)?((?:关联)?(?:来源|出处|参考)|source|references?)\s*[：:]",
    re.IGNORECASE,
)


def list_items(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def normalize_source_note(value: str) -> str:
    match = WIKI_LINK_RE.search(value)
    return (match.group(1) if match else value).strip().removesuffix(".md")


def is_source_note_target(value: str) -> bool:
    normalized = value.replace("\\", "/")
    if normalized.startswith("01_inbox/") or "/source-notes/" in normalized:
        return True
    candidate = VAULT_ROOT / f"{normalized}.md"
    if not candidate.exists():
        return False
    page = load_page(candidate)
    frontmatter = page["frontmatter"] if isinstance(page["frontmatter"], dict) else {}
    return str(frontmatter.get("type") or "").strip() in {"来源", "章节笔记", "文档地图"}


def source_context_lines(body: str) -> list[str]:
    selected: list[str] = []
    in_source_section = False
    source_level = 0
    for line in body.splitlines():
        heading = re.match(r"^(#{1,6})\s+", line)
        if heading:
            level = len(heading.group(1))
            if SOURCE_HEADING_RE.match(line):
                in_source_section = True
                source_level = level
                selected.append(line)
                continue
            if in_source_section and level <= source_level:
                in_source_section = False
        if in_source_section or SOURCE_LINE_RE.match(line):
            selected.append(line)
    return selected


def infer_source_notes(frontmatter: dict[str, object], body: str) -> list[str]:
    trusted_candidates = list_items(frontmatter.get("source_notes")) + list_items(frontmatter.get("source_note"))
    candidates = list(trusted_candidates)
    related_candidates = list_items(frontmatter.get("related_to")) + list_items(frontmatter.get("builds_on"))
    candidates.extend(candidate for candidate in related_candidates if is_source_note_target(normalize_source_note(candidate)))
    for line in source_context_lines(body):
        candidates.extend(candidate for candidate in WIKI_LINK_RE.findall(line) if is_source_note_target(candidate))
    normalized: list[str] = []
    for candidate in candidates:
        value = normalize_source_note(candidate)
        if value and value not in normalized:
            normalized.append(value)
    return normalized


def infer_source_refs(frontmatter: dict[str, object], body: str) -> list[str]:
    refs = list_items(frontmatter.get("source_refs"))
    patterns = [
        re.compile(r"\bpp?\.\s*(\d+)(?:\s*[-–—]\s*(\d+))?", re.IGNORECASE),
        re.compile(r"(?:页码|pages?)\s*[：:]\s*(\d+)(?:\s*[-–—]\s*(\d+))?", re.IGNORECASE),
        re.compile(r"第\s*(\d+)\s*页"),
    ]
    for pattern in patterns:
        for match in pattern.finditer(body):
            start, end = match.group(1), match.group(2) if match.lastindex and match.lastindex >= 2 else None
            value = f"pp.{start}-{end}" if end else f"p.{start}"
            if value not in refs:
                refs.append(value)
    return refs


def candidate_paths(requested_paths: list[str]) -> list[Path]:
    if requested_paths:
        paths: list[Path] = []
        for raw_path in requested_paths:
            candidate = (VAULT_ROOT / raw_path).resolve()
            try:
                candidate.relative_to(VAULT_ROOT)
            except ValueError as exc:
                raise SystemExit(f"path is outside wiki root: {raw_path}") from exc
            if not candidate.is_file() or candidate.suffix.lower() != ".md":
                raise SystemExit(f"markdown page does not exist: {raw_path}")
            paths.append(candidate)
        return paths

    paths = []
    for path in iter_markdown_files():
        page = load_page(path)
        frontmatter = page["frontmatter"] if isinstance(page["frontmatter"], dict) else {}
        rel_path = str(page["rel_path"])
        has_provenance_fields = any(
            frontmatter.get(field)
            for field in ("source_note", "source_notes", "source_refs", "document_map", "provenance_status")
        )
        if str(frontmatter.get("type") or "").strip() in KNOWLEDGE_TYPES and (
            "/syntheses/" in f"/{rel_path}" or has_provenance_fields
        ):
            paths.append(path)
    return sorted(paths, key=lambda item: item.as_posix().lower())


def inspect_page(path: Path, *, apply: bool) -> dict[str, object]:
    page = load_page(path)
    frontmatter = page["frontmatter"] if isinstance(page["frontmatter"], dict) else {}
    body = str(page["body"])
    source_notes = infer_source_notes(frontmatter, body)
    source_refs = infer_source_refs(frontmatter, body)
    status = "complete" if source_notes and source_refs else "partial" if source_notes or source_refs else "missing"

    updates: dict[str, object] = {}
    if source_notes and source_notes != list_items(frontmatter.get("source_notes")):
        updates["source_notes"] = source_notes
    if source_refs and source_refs != list_items(frontmatter.get("source_refs")):
        updates["source_refs"] = source_refs
    if status != "missing" and str(frontmatter.get("provenance_status") or "") != status:
        updates["provenance_status"] = status
    if status != "missing" and str(frontmatter.get("provenance_checked") or "") != today_iso():
        updates["provenance_checked"] = today_iso()

    changed = bool(updates)
    if apply and changed:
        update_page_frontmatter(path, updates)
    return {
        "path": path.relative_to(VAULT_ROOT).as_posix(),
        "status": status,
        "source_notes": source_notes,
        "source_refs": source_refs,
        "would_update": changed,
        "updated": bool(apply and changed),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="审计并迁移旧知识页的结构化出处元数据。")
    parser.add_argument("--apply", action="store_true", help="写入可从现有页面确定的出处字段；默认只审计")
    parser.add_argument("--path", action="append", default=[], help="只处理指定 wiki 相对路径，可重复传入")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="输出格式")
    args = parser.parse_args()

    pages = [inspect_page(path, apply=args.apply) for path in candidate_paths(args.path)]
    summary = {
        "total": len(pages),
        "complete": sum(1 for item in pages if item["status"] == "complete"),
        "partial": sum(1 for item in pages if item["status"] == "partial"),
        "missing": sum(1 for item in pages if item["status"] == "missing"),
        "would_update": sum(1 for item in pages if item["would_update"]),
        "updated": sum(1 for item in pages if item["updated"]),
    }
    payload = {"schema_version": 1, "apply": args.apply, "summary": summary, "pages": pages}
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    print(f"mode={'apply' if args.apply else 'audit'}")
    print(" ".join(f"{key}={value}" for key, value in summary.items()))
    for item in pages:
        if item["status"] != "missing" or item["would_update"]:
            print(f"{item['status']}: {item['path']} notes={len(item['source_notes'])} refs={len(item['source_refs'])}")


if __name__ == "__main__":
    main()
