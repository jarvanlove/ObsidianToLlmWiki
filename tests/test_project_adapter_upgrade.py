from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path


from tests.test_support import load_script_module


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "00_system" / "scripts" / "project_adapter.py"


class ProjectAdapterUpgradeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_script_module(MODULE_PATH, "project_adapter_test_module")

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.repo = root / "repo"
        self.templates = root / "templates"
        self.repo.mkdir()
        (self.templates / "scripts" / "ai").mkdir(parents=True)
        (self.templates / "docs").mkdir()
        (self.templates / "scripts" / "ai" / "managed.py").write_text("version = 1\n", encoding="utf-8")
        (self.templates / "docs" / "customizable.md").write_text("version 1\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_safe_upgrade_updates_unchanged_file_and_stages_modified_conflict(self) -> None:
        first = self.module.apply_adapter_upgrade(self.repo, template_root=self.templates, target_version=1)
        self.assertEqual(first["status"], "current")
        state_path = self.repo / ".obsidiantowiki" / "adapter-state.json"
        self.assertTrue(state_path.exists())

        managed = self.repo / "scripts" / "ai" / "managed.py"
        customized = self.repo / "docs" / "customizable.md"
        customized.write_text("user customization\n", encoding="utf-8")
        (self.templates / "scripts" / "ai" / "managed.py").write_text("version = 2\n", encoding="utf-8")
        (self.templates / "docs" / "customizable.md").write_text("version 2\n", encoding="utf-8")

        upgraded = self.module.apply_adapter_upgrade(self.repo, template_root=self.templates, target_version=2)
        self.assertEqual(upgraded["status"], "conflicts")
        self.assertEqual(managed.read_text(encoding="utf-8"), "version = 2\n")
        self.assertEqual(customized.read_text(encoding="utf-8"), "user customization\n")
        candidate = self.repo / ".obsidiantowiki" / "upgrade-candidates" / "v2" / "docs" / "customizable.md.new"
        self.assertEqual(candidate.read_text(encoding="utf-8"), "version 2\n")

        state = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(state["adapter_version"], 1)
        self.assertEqual(state["target_adapter_version"], 2)
        self.assertEqual(state["conflicts"], ["docs/customizable.md"])

    def test_legacy_matching_installation_can_be_adopted_without_rewrite(self) -> None:
        destination = self.repo / "scripts" / "ai" / "managed.py"
        destination.parent.mkdir(parents=True)
        destination.write_text("version = 1\n", encoding="utf-8")
        second = self.repo / "docs" / "customizable.md"
        second.parent.mkdir()
        second.write_text("version 1\n", encoding="utf-8")

        result = self.module.apply_adapter_upgrade(self.repo, template_root=self.templates, target_version=1)
        self.assertEqual(result["status"], "current")
        self.assertTrue((self.repo / ".obsidiantowiki" / "adapter-state.json").exists())


if __name__ == "__main__":
    unittest.main()
