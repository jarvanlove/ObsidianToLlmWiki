from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "00_system" / "scripts" / "vault_compat.py"


def page(title: str) -> str:
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
        f"# {title}\n"
    )


class VaultCompatibilityCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.vault = Path(self.temp_dir.name)
        self.env = os.environ.copy()
        self.env["OBSIDIAN_WIKI_ROOT"] = str(self.vault)
        self.env["PYTHONIOENCODING"] = "utf-8"

        personal = self.vault / "10_personal"
        personal.mkdir()
        self.legacy_page = personal / "legacy.md"
        self.legacy_page.write_text(page("Legacy"), encoding="utf-8")

        project = self.vault / "20_projects" / "active" / "unregistered"
        project.mkdir(parents=True)
        (project / "索引.md").write_text("# Unregistered\n", encoding="utf-8")

        registry = self.vault / "00_system" / "registry"
        registry.mkdir(parents=True)
        self.project_repo = self.vault.parent / f"{self.vault.name}-repo"
        self.project_repo.mkdir()
        (registry / "projects.json").write_text(
            json.dumps(
                [
                    {
                        "project_slug": "registered",
                        "project_name": "Registered",
                        "project_repo_root": str(self.project_repo),
                    }
                ]
            ),
            encoding="utf-8",
        )
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

    def tearDown(self) -> None:
        shutil.rmtree(self.project_repo, ignore_errors=True)
        self.temp_dir.cleanup()

    def run_compat(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args, "--format", "json"],
            cwd=REPO_ROOT,
            env=self.env,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_report_and_migration_are_non_destructive_and_idempotent(self) -> None:
        original_hash = hashlib.sha256(self.legacy_page.read_bytes()).hexdigest()
        report = self.run_compat("report")
        self.assertEqual(report.returncode, 0, report.stderr)
        payload = json.loads(report.stdout)
        self.assertEqual(payload["vault_schema"]["current"], 0)
        self.assertEqual(payload["vault_schema"]["target"], 1)
        self.assertEqual(payload["vault_schema"]["pending_migrations"], ["0001-initialize-vault-state"])
        self.assertEqual(payload["wiki_projects"]["unregistered"], ["unregistered"])
        self.assertEqual(payload["wiki_projects"]["repositories"][0]["adapter_status"], "not_installed")

        migrated = self.run_compat("migrate", "--apply")
        self.assertEqual(migrated.returncode, 0, migrated.stderr)
        migrated_payload = json.loads(migrated.stdout)
        self.assertEqual(migrated_payload["from_version"], 0)
        self.assertEqual(migrated_payload["to_version"], 1)
        self.assertEqual(migrated_payload["applied"], ["0001-initialize-vault-state"])
        self.assertEqual(hashlib.sha256(self.legacy_page.read_bytes()).hexdigest(), original_hash)

        second = self.run_compat("migrate", "--apply")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(json.loads(second.stdout)["applied"], [])

    def test_newer_vault_version_is_rejected(self) -> None:
        state = self.vault / "00_system" / "registry" / "vault_state.json"
        state.write_text(
            json.dumps({"schema_version": 1, "vault_schema_version": 99, "migration_history": []}),
            encoding="utf-8",
        )
        result = self.run_compat("report")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("newer than this runtime", result.stderr)


if __name__ == "__main__":
    unittest.main()
