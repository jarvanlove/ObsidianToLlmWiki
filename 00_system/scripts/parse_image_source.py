from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import pytesseract
from PIL import Image, ImageOps

from wiki_lib import SCRIPT_DIR, VAULT_ROOT, append_log, load_page, parse_frontmatter, render_markdown, today_iso, write_text

TESSERACT_CANDIDATES = (
    Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
    Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
    Path.home() / "AppData" / "Local" / "Programs" / "Tesseract-OCR" / "tesseract.exe",
)


def resolve_note_path(raw_path: str) -> Path:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate
    return (VAULT_ROOT / candidate).resolve()


def ensure_tesseract() -> str:
    env_cmd = str(Path(shutil.which("tesseract")).resolve()) if shutil.which("tesseract") else ""
    if env_cmd:
        pytesseract.pytesseract.tesseract_cmd = env_cmd
        return env_cmd

    configured = str(Path(pytesseract.pytesseract.tesseract_cmd).expanduser()) if pytesseract.pytesseract.tesseract_cmd else ""
    if configured and Path(configured).exists():
        return configured

    for candidate in TESSERACT_CANDIDATES:
        if candidate.exists():
            pytesseract.pytesseract.tesseract_cmd = str(candidate)
            return str(candidate)

    raise FileNotFoundError("未找到 tesseract 可执行文件。请先安装 Tesseract OCR，或把 tesseract 加入 PATH。")


def preprocess_image(source_path: Path) -> Image.Image:
    image = Image.open(source_path)
    image = ImageOps.exif_transpose(image)
    image = ImageOps.grayscale(image)
    image = ImageOps.autocontrast(image)
    return image


def infer_lang(frontmatter: dict[str, object], explicit_lang: str) -> str:
    if explicit_lang.strip():
        return explicit_lang.strip()
    language = str(frontmatter.get("language") or "").strip().lower()
    if language in {"zh", "zh-cn", "zh-hans", "chi_sim"}:
        return "chi_sim+eng"
    return "eng"


def upsert_section(body: str, heading: str, lines: list[str]) -> str:
    marker = f"## {heading}"
    chunks = body.strip().splitlines()
    start = None
    end = None
    for index, line in enumerate(chunks):
        if line.strip() == marker:
            start = index
            continue
        if start is not None and line.startswith("## "):
            end = index
            break
    replacement = [marker, "", *lines]
    if start is None:
        updated = chunks + ["", *replacement]
    else:
        updated = chunks[:start] + replacement + ([] if end is None else [""] + chunks[end:])
    return "\n".join(updated).rstrip() + "\n"


def build_ocr_lines(text: str, scratch_rel_path: str) -> list[str]:
    if not text.strip():
        return [
            f"- OCR 产物: `{scratch_rel_path}`",
            "- 当前未识别出正文文本。",
        ]
    excerpt = text.strip()[:6000]
    return [
        f"- OCR 产物: `{scratch_rel_path}`",
        "",
        "```text",
        excerpt,
        "```",
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="对图片来源笔记执行 OCR，并回写结果。")
    parser.add_argument("--note", required=True, help="图片来源笔记路径，可为相对 wiki 根目录路径")
    parser.add_argument("--lang", default="", help="可选，显式指定 OCR 语言，例如 eng 或 chi_sim+eng")
    parser.add_argument("--rebuild", action="store_true", help="完成后重建索引")
    args = parser.parse_args()

    note_path = resolve_note_path(args.note)
    if not note_path.exists():
        raise SystemExit(f"来源笔记不存在: {note_path}")

    page = load_page(note_path)
    frontmatter = page["frontmatter"]
    if not isinstance(frontmatter, dict):
        raise SystemExit("来源笔记缺少 frontmatter。")
    if str(frontmatter.get("type") or "").strip() != "来源":
        raise SystemExit("当前页面不是来源笔记。")
    if str(frontmatter.get("media_type") or "").strip() != "image":
        raise SystemExit("当前来源不是图片类型。")

    source_rel_path = str(frontmatter.get("source_path") or "").strip()
    if not source_rel_path:
        raise SystemExit("来源笔记缺少 source_path。")
    source_path = (VAULT_ROOT / source_rel_path).resolve()
    if not source_path.exists():
        raise SystemExit(f"原始图片不存在: {source_path}")

    scratch_dir = VAULT_ROOT / "01_inbox" / "scratch" / "ocr"
    scratch_dir.mkdir(parents=True, exist_ok=True)
    scratch_path = scratch_dir / f"{note_path.stem}.txt"

    try:
        tesseract_cmd = ensure_tesseract()
        image = preprocess_image(source_path)
        ocr_lang = infer_lang(frontmatter, args.lang)
        text = pytesseract.image_to_string(image, lang=ocr_lang).strip()
        write_text(scratch_path, text)

        updated_frontmatter = dict(frontmatter)
        updated_frontmatter["parse_status"] = "已提取"
        updated_frontmatter["has_ocr_text"] = bool(text)
        updated_frontmatter["parse_error"] = ""
        updated_frontmatter["last_parse_attempt"] = today_iso()
        if text and str(updated_frontmatter.get("ingest_status") or "").strip() in {"", "已登记"}:
            updated_frontmatter["ingest_status"] = "已解析"

        body = str(page["body"])
        body = upsert_section(
            body,
            "媒体处理",
            [
                "- 媒体类型: 图片",
                f"- 当前阶段: 已完成 OCR。",
                f"- OCR 引擎: `{Path(tesseract_cmd).name}`",
                f"- OCR 语言: `{ocr_lang}`",
            ],
        )
        body = upsert_section(
            body,
            "OCR 文本",
            build_ocr_lines(text, scratch_path.relative_to(VAULT_ROOT).as_posix()),
        )
        write_text(note_path, render_markdown(updated_frontmatter, body))
        append_log("更新", f"图片 OCR | {page['title']}", f"已写入 OCR 结果到 {scratch_path.relative_to(VAULT_ROOT).as_posix()}")
    except Exception as exc:
        text = note_path.read_text(encoding="utf-8")
        current_frontmatter, body = parse_frontmatter(text)
        current_frontmatter["parse_status"] = "失败"
        current_frontmatter["has_ocr_text"] = False
        current_frontmatter["parse_error"] = str(exc)
        current_frontmatter["last_parse_attempt"] = today_iso()
        body = upsert_section(
            body,
            "媒体处理",
            [
                "- 媒体类型: 图片",
                "- 当前阶段: OCR 失败。",
                f"- 错误: {exc}",
            ],
        )
        write_text(note_path, render_markdown(current_frontmatter, body))
        append_log("更新", f"图片 OCR 失败 | {page['title']}", str(exc))
        raise

    if args.rebuild:
        subprocess.run([sys.executable, str(SCRIPT_DIR / "rebuild_indexes.py")], check=True)

    print(note_path)


if __name__ == "__main__":
    main()
