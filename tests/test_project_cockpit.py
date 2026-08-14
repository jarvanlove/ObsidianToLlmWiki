from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "00_system" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from project_cockpit import AREA_KEYS, build_cockpit  # noqa: E402
from wiki_lib import render_markdown  # noqa: E402


class ProjectCockpitTests(unittest.TestCase):
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
        (self.repo / "TASKS.md").write_text("# Tasks\n\n- [ ] Ship the cockpit.\n", encoding="utf-8")
        receipt_dir = self.repo / ".obsidiantowiki" / "context-receipts"
        receipt_dir.mkdir(parents=True)
        (receipt_dir / "cockpit.json").write_text(
            json.dumps({"status": "ready", "content_hash": "abc123", "task_id": "cockpit"}), encoding="utf-8"
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

    def test_builds_five_safe_areas_with_evidence_drilldown(self) -> None:
        self.card("MILE-1", "milestone", "Memory migration completed.")
        self.card("RISK-1", "open_risk", "Real projects still need explicit migration approval.")
        self.card("RISK-SECRET", "open_risk", r"api_key=top-secret C:\Users\private\source.py")
        self.card("DEC-D1", "decision", "A disputed decision needs review.", status="disputed")

        report = build_cockpit(self.repo)
        payload = json.loads(Path(report["data_path"]).read_text(encoding="utf-8"))
        html = Path(report["html_path"]).read_text(encoding="utf-8")

        self.assertEqual(tuple(payload["areas"]), AREA_KEYS)
        self.assertIn("Memory migration completed.", json.dumps(payload, ensure_ascii=False))
        self.assertIn("RISK-1", html)
        self.assertIn("git diff", html.lower())
        self.assertIn("Context Receipt", html)
        self.assertIn("<details>", html)
        self.assertNotIn(str(self.root), html)
        self.assertNotIn("top-secret", html)
        self.assertNotIn(r"C:\Users\private", html)
        self.assertNotIn("top-secret", json.dumps(payload, ensure_ascii=False))

    def test_empty_areas_say_no_action_required(self) -> None:
        (self.repo / "TASKS.md").write_text("# Tasks\n\n- [x] Done.\n", encoding="utf-8")

        report = build_cockpit(self.repo)
        payload = json.loads(Path(report["data_path"]).read_text(encoding="utf-8"))

        for key in ("recent_changes", "pending_decisions", "open_risks", "next_steps"):
            self.assertEqual(payload["areas"][key]["empty_message"], "无需处理")

    def test_failed_render_leaves_markdown_unchanged(self) -> None:
        before = (self.repo / "TASKS.md").read_bytes()

        with patch("project_cockpit.render_dashboard", side_effect=RuntimeError("template failed")):
            with self.assertRaises(RuntimeError):
                build_cockpit(self.repo)

        self.assertEqual((self.repo / "TASKS.md").read_bytes(), before)
        self.assertFalse((self.repo / ".obsidiantowiki" / "cockpit" / "index.html").exists())

    def test_public_runtime_builds_the_same_static_projection(self) -> None:
        runtime = REPO_ROOT / "00_system" / "scripts" / "otw.py"

        result = subprocess.run(
            [sys.executable, str(runtime), "cockpit", "build", "--repo-root", str(self.repo), "--format", "json"],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )

        self.assertEqual(json.loads(result.stdout)["status"], "built")
        self.assertTrue((self.repo / ".obsidiantowiki" / "cockpit" / "data.json").exists())


if __name__ == "__main__":
    unittest.main()
