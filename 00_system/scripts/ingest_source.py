from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from pptx import Presentation
from pypdf import PdfReader

from create_page import ensure_project
from wiki_lib import (
    SCRIPT_DIR,
    VAULT_ROOT,
    append_log,
    normalize_tags,
    render_template,
    slugify,
    today_iso,
    write_text,
)

TEMPLATE_DIR = VAULT_ROOT / "00_system" / "templates"
TEXT_EXTENSIONS = {".md", ".markdown", ".txt", ".py", ".js", ".ts", ".json", ".yaml", ".yml", ".html", ".css", ".java", ".go", ".rs", ".sql"}


def ensure_project_layout(project_name: str) -> Path:
    return ensure_project(project_name, tags=[], status="活跃", summary=f"{project_name} 的项目知识库。")


def copy_source(source_file: Path, project_name: str | None) -> Path:
    if project_name:
        destination_dir = ensure_project_layout(project_name) / "sources"
    else:
        destination_dir = VAULT_ROOT / "01_inbox" / "raw"
        destination_dir.mkdir(parents=True, exist_ok=True)

    destination = destination_dir / source_file.name
    if source_file.resolve() != destination.resolve():
        shutil.copy2(source_file, destination)
    return destination


def render_source_note(title: str, domain: str, project_slug: str, tags: list[str], summary: str, source_path: str) -> str:
    content = render_template(
        TEMPLATE_DIR / "source-note.md",
        {
            "title": title,
            "type": "来源",
            "domain": domain,
            "project": project_slug,
            "status": "已收录",
            "tags": ", ".join(tags),
            "updated": today_iso(),
            "summary": summary,
        },
    )
    lines = content.splitlines()
    result: list[str] = []
    injected = False
    for line in lines:
        result.append(line)
        if line.strip() == "source_path:":
            result[-1] = f"source_path: {source_path}"
            injected = True
    if not injected:
        result.insert(9, f"source_path: {source_path}")
    return "\n".join(result) + "\n"


def extract_text_from_pptx(path: Path) -> str:
    presentation = Presentation(str(path))
    chunks: list[str] = []
    for slide_index, slide in enumerate(presentation.slides, start=1):
        slide_lines: list[str] = []
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                text = (shape.text or "").strip()
                if text:
                    slide_lines.append(text)
        if slide_lines:
            chunks.append(f"## 第 {slide_index} 页\n\n" + "\n\n".join(slide_lines))
    return "\n\n".join(chunks).strip()


def extract_text_from_docx(path: Path) -> str:
    result = subprocess.run(
        ["pandoc", str(path), "-t", "markdown"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def extract_text_from_pdf(path: Path) -> str:
    try:
        reader = PdfReader(str(path))
    except Exception:
        return ""

    chunks: list[str] = []
    for page_index, page in enumerate(reader.pages, start=1):
        try:
            text = (page.extract_text() or "").strip()
        except Exception:
            text = ""
        if text:
            chunks.append(f"## 第 {page_index} 页\n\n{text}")
    return "\n\n".join(chunks).strip()


def extract_text_content(path: Path) -> tuple[str, str]:
    ext = path.suffix.lower()
    if ext in TEXT_EXTENSIONS:
        try:
            return path.read_text(encoding="utf-8"), "text"
        except UnicodeDecodeError:
            try:
                return path.read_text(encoding="utf-8-sig"), "text"
            except UnicodeDecodeError:
                return "", "binary"
    if ext == ".docx":
        return extract_text_from_docx(path), "docx"
    if ext == ".pptx":
        return extract_text_from_pptx(path), "pptx"
    if ext == ".pdf":
        return extract_text_from_pdf(path), "pdf"
    return "", "binary"


def enrich_source_note(content: str, extracted_text: str, extract_mode: str) -> str:
    lines = content.rstrip().splitlines()
    lines.extend(["", "## 文件识别", "", f"- 识别方式: {extract_mode}"])
    if extracted_text.strip():
        excerpt = extracted_text.strip()[:6000]
        lines.extend(["", "## 提取文本", "", "```text", excerpt, "```"])
    else:
        lines.extend(["", "## 提取文本", "", "- 当前未提取到正文文本。文件已入库，可后续人工补充或扩展解析能力。"])
    return "\n".join(lines) + "\n"


def append_to_project_sources(project_name: str, note_path: Path, stored_source: Path) -> None:
    source_registry = ensure_project_layout(project_name) / "来源.md"
    if not source_registry.exists():
        return

    relative_source = stored_source.relative_to(VAULT_ROOT).as_posix()
    note_target = note_path.relative_to(source_registry.parent).with_suffix("").as_posix()
    entry = f"- [[{note_target}|{note_path.stem}]] | 原文件: `{relative_source}`"
    text = source_registry.read_text(encoding="utf-8")
    if entry not in text:
        source_registry.write_text(text.rstrip() + "\n" + entry + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="把原始资料复制到知识库并生成来源笔记。")
    parser.add_argument("--source", required=True, help="原始文件路径")
    parser.add_argument("--title", default="", help="来源标题，默认取文件名")
    parser.add_argument("--project", default="", help="所属项目名")
    parser.add_argument("--tags", default="", help="英文逗号分隔标签")
    parser.add_argument("--summary", default="", help="一句话摘要")
    args = parser.parse_args()

    source_file = Path(args.source).expanduser().resolve()
    if not source_file.exists():
        raise SystemExit(f"源文件不存在: {source_file}")

    title = args.title.strip() or source_file.stem
    project_name = args.project.strip() or None
    project_slug = slugify(project_name) if project_name else ""
    tags = normalize_tags(args.tags)
    summary = args.summary.strip() or f"{title} 的来源笔记。"

    stored_source = copy_source(source_file, project_name)
    extracted_text, extract_mode = extract_text_content(stored_source)

    if project_name:
        note_dir = ensure_project_layout(project_name) / "source-notes"
        domain = "项目"
    else:
        note_dir = VAULT_ROOT / "01_inbox" / "clips"
        note_dir.mkdir(parents=True, exist_ok=True)
        domain = "个人"

    note_path = note_dir / f"{slugify(title)}.md"
    content = render_source_note(
        title=title,
        domain=domain,
        project_slug=project_slug,
        tags=tags,
        summary=summary,
        source_path=stored_source.relative_to(VAULT_ROOT).as_posix(),
    )
    content = enrich_source_note(content, extracted_text, extract_mode)
    write_text(note_path, content)

    if project_name:
        append_to_project_sources(project_name, note_path, stored_source)

    details = f"来源文件: {stored_source.relative_to(VAULT_ROOT).as_posix()} | 来源笔记: {note_path.relative_to(VAULT_ROOT).as_posix()}"
    append_log("摄入", title, details)
    subprocess.run([sys.executable, str(SCRIPT_DIR / "rebuild_indexes.py")], check=True)
    print(note_path)


if __name__ == "__main__":
    main()

