from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from wiki_lib import parse_frontmatter


AREA_KEYS = ("current_status", "recent_changes", "pending_decisions", "open_risks", "next_steps")
AREA_LABELS = {
    "current_status": "当前状态",
    "recent_changes": "最近变化",
    "pending_decisions": "待决定",
    "open_risks": "开放风险",
    "next_steps": "下一步",
}
SECRET = re.compile(r"(?i)(api[_-]?key|password|secret|token)\s*[:=]\s*\S+")
ABSOLUTE_PATH = re.compile(r"(?:[A-Za-z]:\\[^\s<>'\"]+|/(?:Users|home)/[^\s<>'\"]+)")


def sanitize(value: object) -> str:
    text = SECRET.sub(r"\1=[redacted]", str(value or "").strip())
    return ABSOLUTE_PATH.sub("[local-path]", text)[:500]


def load_context(repo_root: Path) -> tuple[Path, str]:
    try:
        payload = json.loads((repo_root / "wiki.context.json").read_text(encoding="utf-8"))
        return Path(str(payload["wiki_root"])).expanduser().resolve(), str(payload["project_slug"])
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid wiki.context.json: {exc}") from exc


def load_cards(project_root: Path) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for path in sorted((project_root / "memory").glob("*.md")):
        try:
            frontmatter, _body = parse_frontmatter(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError):
            continue
        cards.append({**dict(frontmatter), "relative_path": f"memory/{path.name}"})
    return cards


def latest_context_receipt(repo_root: Path) -> dict[str, Any]:
    directory = repo_root / ".obsidiantowiki" / "context-receipts"
    paths = sorted(directory.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    for path in paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            return {
                "task_id": sanitize(payload.get("task_id")),
                "status": sanitize(payload.get("status")),
                "content_hash": sanitize(payload.get("content_hash")),
                "path": f"context-receipts/{path.name}",
            }
    return {"task_id": "", "status": "missing", "content_hash": "", "path": ""}


def git_state(repo_root: Path) -> dict[str, Any]:
    completed = subprocess.run(
        ["git", "status", "--short"], cwd=repo_root, check=False, capture_output=True, text=True, encoding="utf-8"
    )
    lines = [sanitize(line) for line in completed.stdout.splitlines() if line.strip()]
    return {"changed_count": len(lines), "clean": not lines, "files": lines[:12]}


def task_items(repo_root: Path) -> list[dict[str, str]]:
    path = repo_root / "TASKS.md"
    if not path.exists():
        return []
    items: list[dict[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"\s*- \[ \]\s+(.+)", line)
        if match:
            items.append({"title": sanitize(match.group(1)), "source": "TASKS.md"})
    return items[:12]


def card_item(card: dict[str, Any]) -> dict[str, str]:
    return {
        "id": sanitize(card.get("id")),
        "title": sanitize(card.get("summary") or card.get("title")),
        "date": sanitize(card.get("effective_from")),
        "source": sanitize(card.get("relative_path")),
        "evidence": ", ".join(sanitize(item) for item in card.get("evidence_refs", []) if sanitize(item)),
    }


def build_projection(repo_root: Path) -> dict[str, Any]:
    resolved = repo_root.expanduser().resolve()
    wiki_root, project_slug = load_context(resolved)
    cards = load_cards(wiki_root / "20_projects" / "active" / project_slug)
    receipt = latest_context_receipt(resolved)
    git = git_state(resolved)

    active = [card for card in cards if card.get("status") == "active"]
    recent = [card_item(card) for card in active if card.get("kind") == "milestone"][:8]
    pending = [
        card_item(card)
        for card in cards
        if card.get("status") in {"pending_review", "disputed"}
        or card.get("kind") == "decision" and card.get("status") != "active"
    ][:8]
    risks = [card_item(card) for card in active if card.get("kind") == "open_risk"][:8]
    next_steps = task_items(resolved)
    status_text = "上下文可信，可以继续推进" if receipt["status"] == "ready" else "上下文需要复核"
    current = [
        {
            "title": status_text,
            "source": "Context Receipt",
            "evidence": receipt["content_hash"][:12],
            "detail": receipt["path"] or "尚未生成收据",
        },
        {
            "title": "工作区干净" if git["clean"] else f"工作区有 {git['changed_count']} 项变化",
            "source": "git diff",
            "evidence": "查看变更范围",
            "detail": "；".join(git["files"]) if git["files"] else "没有未提交变化",
        },
    ]
    areas = {
        "current_status": {"label": AREA_LABELS["current_status"], "items": current, "empty_message": "无需处理"},
        "recent_changes": {"label": AREA_LABELS["recent_changes"], "items": recent, "empty_message": "无需处理"},
        "pending_decisions": {"label": AREA_LABELS["pending_decisions"], "items": pending, "empty_message": "无需处理"},
        "open_risks": {"label": AREA_LABELS["open_risks"], "items": risks, "empty_message": "无需处理"},
        "next_steps": {"label": AREA_LABELS["next_steps"], "items": next_steps, "empty_message": "无需处理"},
    }
    return {
        "schema_version": 1,
        "project": sanitize(project_slug),
        "generated_at": datetime.now().astimezone().isoformat(),
        "summary": status_text,
        "receipt": receipt,
        "areas": areas,
    }


def concise_status(payload: dict[str, Any]) -> str:
    lines = [f"当前状态：{payload['summary']}"]
    for key in ("next_steps", "open_risks", "pending_decisions"):
        area = payload["areas"][key]
        item = area["items"][0]["title"] if area["items"] else area["empty_message"]
        lines.append(f"{area['label']}：{item}")
    receipt = payload["receipt"]
    lines.append(f"Context Receipt：{receipt.get('content_hash') or '尚未生成'}")
    return "\n".join(lines)
