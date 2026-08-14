from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "00_system" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from project_status import AREA_KEYS, build_projection, concise_status  # noqa: E402
from wiki_lib import render_markdown  # noqa: E402


class ProjectStatusTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.repo = self.root / "repo"
        self.vault = self.root / "vault"
        self.project = self.vault / "20_projects" / "active" / "demo"
        self.memory = self.project / "memory"
        self.repo.mkdir()
        self.memory.mkdir(parents=True)
        (self.repo / "wiki.context.json").write_text(
            json.dumps({"wiki_root": str(self.vault), "project_slug": "demo"}), encoding="utf-8"
        )
        (self.repo / "TASKS.md").write_text("# Tasks\n\n- [ ] Verify status.\n", encoding="utf-8")
        receipt_dir = self.repo / ".obsidiantowiki" / "context-receipts"
        receipt_dir.mkdir(parents=True)
        (receipt_dir / "status.json").write_text(
            json.dumps({"status": "ready", "content_hash": "abc123", "task_id": "status"}), encoding="utf-8"
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def card(self, card_id: str, kind: str, summary: str, *, status: str = "active") -> None:
        frontmatter = {
            "title": summary,
            "type": "项目记忆卡",
            "domain": "项目",
            "project": "demo",
            "id": card_id,
            "stable_key": card_id.lower(),
            "kind": kind,
            "status": status,
            "effective_from": "2026-08-13",
            "summary": summary,
            "evidence_refs": ["git:abc123"],
        }
        (self.memory / f"{card_id}.md").write_text(
            render_markdown(frontmatter, f"# {summary}\n\n{summary}"), encoding="utf-8"
        )

    def test_builds_privacy_bounded_status_without_writing_html(self) -> None:
        self.card("MILE-1", "milestone", "Memory migration completed.")
        self.card("RISK-1", "open_risk", "Real projects still need explicit approval.")
        self.card("RISK-SECRET", "open_risk", r"api_key=top-secret C:\Users\private\source.py")

        payload = build_projection(self.repo)
        rendered = json.dumps(payload, ensure_ascii=False)

        self.assertEqual(tuple(payload["areas"]), AREA_KEYS)
        self.assertIn("Memory migration completed.", rendered)
        self.assertNotIn("top-secret", rendered)
        self.assertNotIn(str(self.root), rendered)
        self.assertFalse((self.repo / ".obsidiantowiki" / "cockpit").exists())

    def test_concise_status_keeps_context_receipt_and_next_action(self) -> None:
        text = concise_status(build_projection(self.repo))

        self.assertIn("当前状态", text)
        self.assertIn("Verify status.", text)
        self.assertIn("Context Receipt", text)
        self.assertIn("abc123", text)


if __name__ == "__main__":
    unittest.main()
