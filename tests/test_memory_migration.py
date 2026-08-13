from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "00_system" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from migrate_project_memory import CORE_PAGE_NAMES, migrate_project_memory, restore_migration  # noqa: E402
from wiki_lib import parse_frontmatter  # noqa: E402


class MemoryMigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.repo = self.root / "repo"
        self.vault = self.root / "vault"
        self.project = self.vault / "20_projects" / "active" / "demo"
        self.repo.mkdir()
        self.project.mkdir(parents=True)
        (self.repo / "wiki.context.json").write_text(
            json.dumps({"wiki_root": str(self.vault), "project_slug": "demo"}), encoding="utf-8"
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def seed_pages(self, body: str) -> dict[str, bytes]:
        originals: dict[str, bytes] = {}
        for name in CORE_PAGE_NAMES:
            content = f"---\ntitle: {name[:-3]}\nproject: demo\n---\n# {name[:-3]}\n\n{body}\n"
            path = self.project / name
            path.write_text(content, encoding="utf-8")
            originals[name] = path.read_bytes()
        return originals

    def test_dry_run_is_read_only_and_reports_long_project(self) -> None:
        originals = self.seed_pages("legacy " * 22000)
        before = {name: hashlib.sha256(value).hexdigest() for name, value in originals.items()}

        report = migrate_project_memory(self.repo, apply=False, today=date(2026, 8, 13))

        after = {name: hashlib.sha256((self.project / name).read_bytes()).hexdigest() for name in CORE_PAGE_NAMES}
        self.assertEqual(report["status"], "dry_run")
        self.assertEqual(report["classification"], "long")
        self.assertEqual(before, after)
        self.assertFalse((self.project / "memory").exists())

    def test_apply_backs_up_originals_creates_review_snapshots_and_is_idempotent(self) -> None:
        originals = self.seed_pages("A confirmed-looking but untrusted legacy statement.")

        first = migrate_project_memory(self.repo, apply=True, today=date(2026, 8, 13))
        manifest = Path(first["manifest"])
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        cards = sorted((self.project / "memory").glob("LEGACY-*.md"))

        self.assertEqual(first["status"], "applied")
        self.assertEqual(len(cards), 7)
        self.assertTrue(all(parse_frontmatter(path.read_text(encoding="utf-8"))[0]["status"] == "pending_review" for path in cards))
        for name, original in originals.items():
            backup = self.project / payload["backups"][name]
            self.assertEqual(backup.read_bytes(), original)
            self.assertIn("原始页面备份", (self.project / name).read_text(encoding="utf-8"))

        second = migrate_project_memory(self.repo, apply=True, today=date(2026, 8, 13))
        self.assertEqual(second["status"], "unchanged")

    def test_apply_preserves_user_customization_as_conflict(self) -> None:
        self.seed_pages("Legacy content.")
        first = migrate_project_memory(self.repo, apply=True, today=date(2026, 8, 13))
        overview = self.project / "概览.md"
        overview.write_text(overview.read_text(encoding="utf-8") + "\nUser customization.\n", encoding="utf-8")

        second = migrate_project_memory(self.repo, apply=True, today=date(2026, 8, 13))

        self.assertEqual(second["status"], "conflict")
        self.assertIn("概览.md", second["conflicts"])
        self.assertIn("User customization.", overview.read_text(encoding="utf-8"))

    def test_restore_recovers_every_original_byte(self) -> None:
        originals = self.seed_pages("Legacy content to restore.")
        applied = migrate_project_memory(self.repo, apply=True, today=date(2026, 8, 13))

        restored = restore_migration(Path(applied["manifest"]))

        self.assertEqual(restored["status"], "restored")
        for name, original in originals.items():
            self.assertEqual((self.project / name).read_bytes(), original)

    def test_empty_template_uses_local_controls_without_inventing_active_facts(self) -> None:
        self.seed_pages("待补充。")
        (self.repo / "PRODUCT_SPEC.md").write_text("# Product\n\nBuild a controlled AI workflow.\n", encoding="utf-8")
        (self.repo / "ARCHITECTURE.md").write_text("# Architecture\n\nUse evidence gates.\n", encoding="utf-8")

        report = migrate_project_memory(self.repo, apply=True, today=date(2026, 8, 13))
        cards = sorted((self.project / "memory").glob("CONTROL-*.md"))

        self.assertEqual(report["classification"], "template")
        self.assertTrue(cards)
        self.assertTrue(all(parse_frontmatter(path.read_text(encoding="utf-8"))[0]["status"] == "pending_review" for path in cards))
        combined = "\n".join((self.project / name).read_text(encoding="utf-8") for name in CORE_PAGE_NAMES)
        self.assertNotIn("Build a controlled AI workflow.", combined)

    def test_public_runtime_exposes_compile_and_migration_dry_run(self) -> None:
        self.seed_pages("Legacy content.")
        before = (self.project / "概览.md").read_bytes()
        runtime = REPO_ROOT / "00_system" / "scripts" / "otw.py"

        migrated = subprocess.run(
            [sys.executable, str(runtime), "memory", "migrate", "--repo-root", str(self.repo), "--dry-run"],
            check=True,
            capture_output=True,
            text=True,
        )
        compiled = subprocess.run(
            [sys.executable, str(runtime), "memory", "compile", "--repo-root", str(self.repo), "--dry-run"],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertEqual(json.loads(migrated.stdout)["status"], "dry_run")
        self.assertEqual(json.loads(compiled.stdout)["status"], "dry_run")
        self.assertEqual((self.project / "概览.md").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
