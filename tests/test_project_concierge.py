from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "00_system" / "scripts" / "handle_nl_request.py"


class ProjectConciergeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.repo = self.root / "repo"
        self.vault = self.root / "vault"
        project = self.vault / "20_projects" / "active" / "demo"
        (project / "memory").mkdir(parents=True)
        self.repo.mkdir()
        (self.repo / "wiki.context.json").write_text(
            json.dumps({"wiki_root": str(self.vault), "project_slug": "demo"}), encoding="utf-8"
        )
        (self.repo / "TASKS.md").write_text("# Tasks\n\n- [ ] Verify status.\n", encoding="utf-8")
        receipt_dir = self.repo / ".obsidiantowiki" / "context-receipts"
        receipt_dir.mkdir(parents=True)
        (receipt_dir / "latest.json").write_text(
            json.dumps({"status": "ready", "content_hash": "receipt-hash", "task_id": "latest"}), encoding="utf-8"
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_status_question_uses_read_only_projection_and_cites_context_receipt(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--request",
                "项目现在怎么样",
                "--repo-root",
                str(self.repo),
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"},
        )

        self.assertIn("当前状态", result.stdout)
        self.assertIn("Verify status.", result.stdout)
        self.assertIn("Context Receipt", result.stdout)
        self.assertIn("receipt-hash", result.stdout)
        self.assertFalse((self.repo / ".obsidiantowiki" / "cockpit").exists())


if __name__ == "__main__":
    unittest.main()
