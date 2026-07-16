from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.test_support import load_script_module


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "00_system" / "scripts"
BUILD_SCRIPT = SCRIPT_DIR / "build_retrieval_index.py"
INGEST_SCRIPT = SCRIPT_DIR / "ingest_source.py"
wiki_lib = load_script_module(SCRIPT_DIR / "wiki_lib.py", "wiki_lib_private_policy_test_module")


def page(title: str, body: str) -> str:
    return (
        "---\n"
        f"title: {title}\n"
        "type: 概念\n"
        "domain: 个人\n"
        "status: 常青\n"
        "updated: 2026-07-16\n"
        f"summary: {title}。\n"
        "tags: []\n"
        "---\n\n"
        f"# {title}\n\n{body}\n"
    )


class PrivatePolicyCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.vault = Path(self.temp_dir.name)
        self.env = os.environ.copy()
        self.env["OBSIDIAN_WIKI_ROOT"] = str(self.vault)
        self.env["PYTHONIOENCODING"] = "utf-8"
        self.index_path = self.vault / ".cache" / "retrieval.sqlite3"

        personal = self.vault / "10_personal"
        personal.mkdir()
        self.visible = personal / "visible.md"
        self.secret = personal / "secret.md"
        self.visible.write_text(page("Visible", "public marker"), encoding="utf-8")
        self.secret.write_text(page("Secret", "secret marker"), encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def run_script(self, script: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(script), *args],
            cwd=REPO_ROOT,
            env=self.env,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def write_policy(self, *, paths: list[str], globs: list[str] | None = None) -> None:
        (self.vault / "wiki.private.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "ai_access": {
                        "excluded_paths": paths,
                        "excluded_globs": globs or [],
                    },
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def test_policy_removes_previously_indexed_page_and_keeps_manual_file(self) -> None:
        first = self.run_script(BUILD_SCRIPT, "--index-path", str(self.index_path))
        self.assertEqual(first.returncode, 0, first.stderr)

        self.write_policy(paths=["10_personal/secret.md"])
        second = self.run_script(BUILD_SCRIPT, "--index-path", str(self.index_path))
        self.assertEqual(second.returncode, 0, second.stderr)
        payload = json.loads(second.stdout)
        self.assertEqual(payload["deleted"], 1)
        self.assertTrue(self.secret.exists())

        with sqlite3.connect(self.index_path) as connection:
            paths = {row[0] for row in connection.execute("SELECT rel_path FROM pages")}
        self.assertIn("10_personal/visible.md", paths)
        self.assertNotIn("10_personal/secret.md", paths)

    def test_excluded_raw_source_is_rejected_before_ingestion(self) -> None:
        raw = self.vault / "01_inbox" / "raw" / "credentials.txt"
        raw.parent.mkdir(parents=True)
        raw.write_text("local-only-value\n", encoding="utf-8")
        self.write_policy(paths=["01_inbox/raw/credentials.txt"])

        result = self.run_script(INGEST_SCRIPT, "--source", str(raw), "--title", "credentials")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("AI access policy", result.stderr)
        self.assertFalse((self.vault / "01_inbox" / "clips" / "credentials.md").exists())

    def test_malformed_policy_fails_closed(self) -> None:
        (self.vault / "wiki.private.json").write_text("{broken", encoding="utf-8")
        result = self.run_script(BUILD_SCRIPT, "--index-path", str(self.index_path))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("wiki.private.json", result.stderr)

    def test_dotfiles_and_directory_subtrees_can_be_excluded_exactly(self) -> None:
        self.write_policy(paths=[".env", "01_inbox/raw/private"])
        policy = wiki_lib.load_private_policy(self.vault)
        self.assertTrue(wiki_lib.is_ai_access_excluded(self.vault / ".env", vault_root=self.vault, policy=policy))
        self.assertTrue(
            wiki_lib.is_ai_access_excluded(
                self.vault / "01_inbox" / "raw" / "private" / "nested.txt",
                vault_root=self.vault,
                policy=policy,
            )
        )
        self.assertFalse(
            wiki_lib.is_ai_access_excluded(
                self.vault / "01_inbox" / "raw" / "private-notes" / "visible.txt",
                vault_root=self.vault,
                policy=policy,
            )
        )


if __name__ == "__main__":
    unittest.main()
