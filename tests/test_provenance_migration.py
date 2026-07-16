from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATION_SCRIPT = REPO_ROOT / "00_system" / "scripts" / "migrate_provenance.py"


def synthesis(title: str, body: str) -> str:
    return (
        "---\n"
        f"title: {title}\n"
        "type: 综述\n"
        "domain: 个人\n"
        "status: 常青\n"
        "updated: 2026-01-01\n"
        f"summary: {title} 摘要。\n"
        "tags: []\n"
        "---\n\n"
        f"# {title}\n\n{body}\n"
    )


def frontmatter(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    block = text.split("---", 2)[1]
    payload = yaml.safe_load(block)
    return payload if isinstance(payload, dict) else {}


class ProvenanceMigrationCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.vault = Path(self.temp_dir.name)
        self.env = os.environ.copy()
        self.env["OBSIDIAN_WIKI_ROOT"] = str(self.vault)
        self.env["PYTHONIOENCODING"] = "utf-8"
        syntheses = self.vault / "10_personal" / "syntheses"
        syntheses.mkdir(parents=True)

        self.complete_page = syntheses / "完整出处.md"
        self.complete_page.write_text(
            synthesis(
                "完整出处",
                "> 来源：[[01_inbox/clips/guide|Guide]]\n> 页码：12-14\n\n## 结论\n\n可追溯结论。",
            ),
            encoding="utf-8",
        )
        self.partial_page = syntheses / "部分出处.md"
        self.partial_page.write_text(
            synthesis(
                "部分出处",
                (
                    "> 来源：[[01_inbox/clips/long-guide|Long Guide]]（114页）\n\n"
                    "## 来源\n\n- [[10_personal/entities/openclaw|OpenClaw]]\n\n"
                    "## 结论\n\n没有章节页码。"
                ),
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def run_migration(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(MIGRATION_SCRIPT), "--format", "json", *args],
            cwd=REPO_ROOT,
            env=self.env,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_audit_does_not_write_and_apply_migrates_only_explicit_evidence(self) -> None:
        before = self.complete_page.read_text(encoding="utf-8")
        audit = self.run_migration()
        self.assertEqual(audit.returncode, 0, audit.stderr)
        audit_payload = json.loads(audit.stdout)
        self.assertEqual(audit_payload["summary"]["complete"], 1)
        self.assertEqual(audit_payload["summary"]["partial"], 1)
        self.assertEqual(self.complete_page.read_text(encoding="utf-8"), before)

        applied = self.run_migration("--apply")
        self.assertEqual(applied.returncode, 0, applied.stderr)
        applied_payload = json.loads(applied.stdout)
        self.assertEqual(applied_payload["summary"]["updated"], 2)

        complete = frontmatter(self.complete_page)
        self.assertEqual(complete["source_notes"], ["01_inbox/clips/guide"])
        self.assertEqual(complete["source_refs"], ["pp.12-14"])
        self.assertEqual(complete["provenance_status"], "complete")
        self.assertEqual(str(complete["updated"]), "2026-01-01")

        partial = frontmatter(self.partial_page)
        self.assertEqual(partial["source_notes"], ["01_inbox/clips/long-guide"])
        self.assertNotIn("source_refs", partial)
        self.assertEqual(partial["provenance_status"], "partial")

        second = self.run_migration("--apply")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(json.loads(second.stdout)["summary"]["updated"], 0)


if __name__ == "__main__":
    unittest.main()
