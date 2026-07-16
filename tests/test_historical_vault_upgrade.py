from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "00_system" / "scripts"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class HistoricalVaultUpgradeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.vault = Path(self.temp_dir.name)
        self.env = os.environ.copy()
        self.env["OBSIDIAN_WIKI_ROOT"] = str(self.vault)
        self.env["PYTHONIOENCODING"] = "utf-8"

        registry = self.vault / "00_system" / "registry"
        registry.mkdir(parents=True)
        (registry / "projects.json").write_text("[]\n", encoding="utf-8")
        (registry / "page_schemas.json").write_text(
            json.dumps(
                {
                    "default_required": ["title", "type", "domain", "status", "updated", "summary"],
                    "type_rules": {"概念": {"domain": ["个人"]}},
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        page = self.vault / "10_personal" / "legacy-source-note.md"
        page.parent.mkdir(parents=True)
        page.write_text(
            "---\n"
            "title: Legacy source note\n"
            "type: 概念\n"
            "domain: 个人\n"
            "status: 常青\n"
            "updated: 2026-01-01\n"
            "summary: LegacyCompatibilityToken historical page.\n"
            "tags: []\n"
            "source_note: 01_inbox/clips/legacy-source\n"
            "---\n\n"
            "# Legacy source note\n\nLegacyCompatibilityToken\n",
            encoding="utf-8",
        )
        self.legacy_page = page

        manifest = json.loads((REPO_ROOT / "00_system" / "registry" / "shared_assets.json").read_text(encoding="utf-8"))
        self.shared_rel = Path(manifest["assets"][0]["path"])
        self.shared_page = self.vault / self.shared_rel
        self.shared_page.parent.mkdir(parents=True, exist_ok=True)
        self.shared_page.write_text("# Local customized historical protocol\n", encoding="utf-8")
        self.original_hashes = {path: digest(path) for path in (self.legacy_page, self.shared_page)}

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def run_script(self, name: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPTS / name), *args],
            cwd=REPO_ROOT,
            env=self.env,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_upgrade_preserves_history_and_keeps_legacy_provenance_searchable(self) -> None:
        migrate = self.run_script("vault_compat.py", "migrate", "--apply", "--format", "json")
        self.assertEqual(migrate.returncode, 0, migrate.stderr)

        staged = self.run_script(
            "shared_assets.py",
            "stage",
            "--vault-root",
            str(self.vault),
            "--source-root",
            str(REPO_ROOT),
            "--format",
            "json",
        )
        self.assertEqual(staged.returncode, 0, staged.stderr)
        staged_payload = json.loads(staged.stdout)
        self.assertGreaterEqual(staged_payload["summary"]["conflicts"], 1)
        candidate = self.vault / "40_outputs" / "upgrade-candidates" / "shared" / "v1" / Path(
            f"{self.shared_rel.as_posix()}.new"
        )
        self.assertTrue(candidate.exists())

        index_path = self.vault / "00_system" / "retrieval" / "historical.sqlite3"
        built = self.run_script("build_retrieval_index.py", "--full", "--index-path", str(index_path))
        self.assertEqual(built.returncode, 0, built.stderr)
        searched = self.run_script(
            "search_wiki.py",
            "LegacyCompatibilityToken",
            "--format",
            "json",
            "--index-path",
            str(index_path),
            "--no-refresh",
        )
        self.assertEqual(searched.returncode, 0, searched.stderr)
        results = json.loads(searched.stdout)["results"]
        self.assertTrue(results)
        self.assertEqual(results[0]["source_notes"], ["01_inbox/clips/legacy-source"])

        for path, original_hash in self.original_hashes.items():
            self.assertEqual(digest(path), original_hash)

        second = self.run_script("vault_compat.py", "migrate", "--apply", "--format", "json")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(json.loads(second.stdout)["applied"], [])


if __name__ == "__main__":
    unittest.main()
