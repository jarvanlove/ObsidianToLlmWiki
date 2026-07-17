from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests.test_support import load_script_module


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "00_system" / "scripts" / "shared_assets.py"


class SharedAssetUpgradeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_script_module(MODULE_PATH, "shared_assets_test_module")

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.source = root / "source"
        self.vault = root / "vault"
        self.source.mkdir()
        self.vault.mkdir()
        self.rel_path = "30_shared/architectures/protocol.md"
        source_file = self.source / self.rel_path
        private_file = self.vault / self.rel_path
        source_file.parent.mkdir(parents=True)
        private_file.parent.mkdir(parents=True)
        source_file.write_text("version 1\n", encoding="utf-8")
        private_file.write_text("version 1\n", encoding="utf-8")
        state = self.vault / "00_system" / "registry" / "vault_state.json"
        state.parent.mkdir(parents=True)
        state.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "vault_schema_version": 1,
                    "migration_history": [],
                    "shared_assets": {},
                }
            ),
            encoding="utf-8",
        )
        self.assets = [{"path": self.rel_path, "version": 1}]

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_safe_update_requires_recorded_unchanged_baseline(self) -> None:
        staged = self.module.apply_shared_asset_action(
            "stage",
            vault_root=self.vault,
            source_root=self.source,
            release_version=1,
            assets=self.assets,
        )
        self.assertEqual(staged["summary"]["current"], 1)

        (self.source / self.rel_path).write_text("version 2\n", encoding="utf-8")
        upgraded = self.module.apply_shared_asset_action(
            "apply-safe",
            vault_root=self.vault,
            source_root=self.source,
            release_version=2,
            assets=[{"path": self.rel_path, "version": 2}],
        )
        self.assertEqual(upgraded["summary"]["updated"], 1)
        self.assertEqual((self.vault / self.rel_path).read_text(encoding="utf-8"), "version 2\n")

    def test_user_modified_asset_is_preserved_and_new_version_is_staged(self) -> None:
        self.module.apply_shared_asset_action(
            "stage",
            vault_root=self.vault,
            source_root=self.source,
            release_version=1,
            assets=self.assets,
        )
        private_file = self.vault / self.rel_path
        private_file.write_text("user customization\n", encoding="utf-8")
        (self.source / self.rel_path).write_text("version 2\n", encoding="utf-8")

        result = self.module.apply_shared_asset_action(
            "apply-safe",
            vault_root=self.vault,
            source_root=self.source,
            release_version=2,
            assets=[{"path": self.rel_path, "version": 2}],
        )
        self.assertEqual(result["summary"]["conflicts"], 1)
        self.assertEqual(private_file.read_text(encoding="utf-8"), "user customization\n")
        candidate = self.vault / "40_outputs" / "upgrade-candidates" / "shared" / "v2" / f"{self.rel_path}.new"
        self.assertEqual(candidate.read_text(encoding="utf-8"), "version 2\n")

        resolved = self.module.resolve_shared_asset(
            vault_root=self.vault,
            source_root=self.source,
            release_version=2,
            assets=[{"path": self.rel_path, "version": 2}],
            rel_path=self.rel_path,
            resolution="keep-local",
        )
        self.assertEqual(resolved["status"], "resolved_local")
        self.assertIn("keep-local", self.module.render_text(resolved))
        self.assertFalse(candidate.exists())
        repeated = self.module.apply_shared_asset_action(
            "stage",
            vault_root=self.vault,
            source_root=self.source,
            release_version=2,
            assets=[{"path": self.rel_path, "version": 2}],
        )
        self.assertEqual(repeated["summary"]["resolved_local"], 1)
        self.assertEqual(repeated["summary"]["staged"], 0)

        (self.vault / self.rel_path).write_text("local change after review\n", encoding="utf-8")
        local_changed = self.module.apply_shared_asset_action(
            "stage",
            vault_root=self.vault,
            source_root=self.source,
            release_version=2,
            assets=[{"path": self.rel_path, "version": 2}],
        )
        self.assertEqual(local_changed["summary"]["conflicts"], 1)
        self.assertTrue(candidate.exists())
        self.module.resolve_shared_asset(
            vault_root=self.vault,
            source_root=self.source,
            release_version=2,
            assets=[{"path": self.rel_path, "version": 2}],
            rel_path=self.rel_path,
            resolution="keep-local",
        )

        (self.source / self.rel_path).write_text("version 3\n", encoding="utf-8")
        changed = self.module.apply_shared_asset_action(
            "stage",
            vault_root=self.vault,
            source_root=self.source,
            release_version=3,
            assets=[{"path": self.rel_path, "version": 3}],
        )
        self.assertEqual(changed["summary"]["conflicts"], 1)
        self.assertTrue(
            (self.vault / "40_outputs" / "upgrade-candidates" / "shared" / "v3" / f"{self.rel_path}.new").exists()
        )


if __name__ == "__main__":
    unittest.main()
