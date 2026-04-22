from __future__ import annotations

import json
import os
import re
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_VAULT_ROOT = SCRIPT_DIR.parent.parent
VAULT_ROOT = Path(os.environ.get("OBSIDIAN_WIKI_ROOT", str(DEFAULT_VAULT_ROOT))).resolve()
LOG_PATH = VAULT_ROOT / "log.md"
USER_WIKI_CONFIG_CANDIDATES = (
    Path.home() / ".obsidiantowiki.json",
    Path.home() / ".config" / "obsidiantowiki" / "config.json",
)

EXCLUDED_PARTS = {
    ".obsidian",
    "__pycache__",
    "docs",
}

EXCLUDED_PATH_SNIPPETS = (
    "00_system/templates/",
)


def today_iso() -> str:
    return date.today().isoformat()


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r'[<>:"/\\\\|?*]+', " ", value)
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"[^\w\u4e00-\u9fff-]+", "", value, flags=re.UNICODE)
    value = re.sub(r"-{2,}", "-", value).strip("-._ ")
    return value or "未命名"


def normalize_tags(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [tag.strip() for tag in raw.split(",") if tag.strip()]


def format_tags(tags: list[str]) -> str:
    return ", ".join(tags)


def parse_frontmatter(text: str) -> tuple[dict[str, object], str]:
    if not text.startswith("---\n"):
        return {}, text

    marker = "\n---\n"
    end_offset = text.find(marker, 4)
    if end_offset == -1:
        return {}, text

    raw_frontmatter = text[4:end_offset]
    body = text[end_offset + len(marker) :].lstrip()
    try:
        loaded = yaml.safe_load(raw_frontmatter) or {}
    except yaml.YAMLError:
        return {}, text

    if not isinstance(loaded, dict):
        return {}, text

    frontmatter = dict(loaded)
    return frontmatter, body


def extract_summary(body: str) -> str:
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("- ") or line.startswith("```"):
            continue
        return line[:180]
    return ""


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def user_wiki_config_path() -> Path:
    for candidate in USER_WIKI_CONFIG_CANDIDATES:
        if candidate.exists():
            return candidate
    return USER_WIKI_CONFIG_CANDIDATES[0]


def load_user_wiki_config() -> dict[str, object]:
    config_path = user_wiki_config_path()
    if not config_path.exists():
        return {}
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def save_user_wiki_config(payload: dict[str, object]) -> Path:
    config_path = user_wiki_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return config_path


def persist_user_wiki_root(wiki_root: Path) -> Path:
    resolved_root = wiki_root.expanduser().resolve()
    config = load_user_wiki_config()
    known_roots = config.get("known_wiki_roots")
    if not isinstance(known_roots, list):
        known_roots = []

    normalized_roots: list[str] = []
    for item in known_roots:
        raw = str(item or "").strip()
        if raw and raw not in normalized_roots:
            normalized_roots.append(raw)

    wiki_root_str = str(resolved_root)
    if wiki_root_str not in normalized_roots:
        normalized_roots.append(wiki_root_str)

    config["default_wiki_root"] = wiki_root_str
    config["last_wiki_root"] = wiki_root_str
    config["known_wiki_roots"] = normalized_roots
    return save_user_wiki_config(config)


def _load_project_context_wiki_root(repo_root: Path | None) -> Path | None:
    if repo_root is None:
        return None
    context_path = repo_root / "wiki.context.json"
    if not context_path.exists():
        return None
    try:
        payload = json.loads(context_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    raw_root = str(payload.get("wiki_root") or "").strip()
    if not raw_root:
        return None
    candidate = Path(raw_root).expanduser().resolve()
    return candidate if candidate.exists() else None


def detect_wiki_root(repo_root: Path | None = None, explicit_root: str | Path | None = None) -> Path:
    if explicit_root:
        candidate = Path(str(explicit_root)).expanduser().resolve()
        if candidate.exists():
            return candidate

    env_root = os.environ.get("OBSIDIAN_WIKI_ROOT", "").strip()
    if env_root:
        candidate = Path(env_root).expanduser().resolve()
        if candidate.exists():
            return candidate

    project_context_root = _load_project_context_wiki_root(repo_root)
    if project_context_root is not None:
        return project_context_root

    config = load_user_wiki_config()
    default_wiki_root = str(config.get("default_wiki_root") or "").strip()
    if default_wiki_root:
        candidate = Path(default_wiki_root).expanduser().resolve()
        if candidate.exists():
            return candidate

    last_wiki_root = str(config.get("last_wiki_root") or "").strip()
    if last_wiki_root:
        candidate = Path(last_wiki_root).expanduser().resolve()
        if candidate.exists():
            return candidate

    if repo_root is not None:
        sibling_private = repo_root.parent / "ObsidianToWiki-private"
        if sibling_private.exists():
            return sibling_private.resolve()

    sibling_private = VAULT_ROOT.parent / f"{VAULT_ROOT.name}-private"
    if sibling_private.exists():
        return sibling_private.resolve()

    if VAULT_ROOT.exists():
        return VAULT_ROOT

    raise FileNotFoundError("未找到可用的 wiki 根目录，请首次明确提供一次私有 wiki 位置。")


def dump_frontmatter(frontmatter: dict[str, object]) -> str:
    return yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False).strip()


def render_markdown(frontmatter: dict[str, object], body: str) -> str:
    return f"---\n{dump_frontmatter(frontmatter)}\n---\n\n{body.strip()}\n"


def update_page_frontmatter(path: Path, updates: dict[str, object]) -> None:
    text = read_text(path)
    frontmatter, body = parse_frontmatter(text)
    merged = dict(frontmatter)
    merged.update(updates)
    write_text(path, render_markdown(merged, body))


def render_template(template_path: Path, variables: dict[str, str]) -> str:
    content = read_text(template_path)
    for key, value in variables.items():
        content = content.replace("{{" + key + "}}", value)
    return content


def iter_markdown_files() -> Iterable[Path]:
    for path in VAULT_ROOT.rglob("*.md"):
        rel_path = path.relative_to(VAULT_ROOT).as_posix()
        if any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        if any(snippet in rel_path for snippet in EXCLUDED_PATH_SNIPPETS):
            continue
        yield path


def obsidian_target(path: Path) -> str:
    return path.relative_to(VAULT_ROOT).with_suffix("").as_posix()


def obsidian_link(path: Path, label: str | None = None) -> str:
    target = obsidian_target(path)
    if label:
        return f"[[{target}|{label}]]"
    return f"[[{target}]]"


def load_page(path: Path) -> dict[str, object]:
    text = read_text(path)
    frontmatter, body = parse_frontmatter(text)
    rel_path = path.relative_to(VAULT_ROOT).as_posix()
    title = str(frontmatter.get("title") or path.stem.replace("-", " "))
    summary = str(frontmatter.get("summary") or extract_summary(body))
    tags = frontmatter.get("tags")
    if not isinstance(tags, list):
        tags = []
    return {
        "path": path,
        "rel_path": rel_path,
        "title": title,
        "summary": summary,
        "frontmatter": frontmatter,
        "body": body,
        "tags": tags,
    }


def append_log(kind: str, title: str, details: str = "", actor: str = "agent") -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not LOG_PATH.exists():
        write_text(LOG_PATH, "# 日志\n")

    timestamp = now_iso()
    entry = f"## [{timestamp}] {kind} | {title}\n\n- actor: {actor}\n"
    if details:
        entry += f"- details: {details}\n"
    entry += "\n"

    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(entry)


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def grouped(items: list[dict[str, object]], key_name: str) -> dict[str, list[dict[str, object]]]:
    groups: dict[str, list[dict[str, object]]] = {}
    for item in items:
        frontmatter = item.get("frontmatter", {})
        if not isinstance(frontmatter, dict):
            continue
        key = str(frontmatter.get(key_name) or "unknown")
        groups.setdefault(key, []).append(item)
    return groups
