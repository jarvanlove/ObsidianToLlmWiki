from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "00_system" / "scripts" / "private_vault.py"


class PrivateVaultSetupTests(unittest.TestCase):
    def run_setup(self, private_root: Path, home: Path) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.update({"HOME": str(home), "USERPROFILE": str(home), "PYTHONIOENCODING": "utf-8"})
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--source-root",
                str(REPO_ROOT),
                "--private-root",
                str(private_root),
                "--format",
                "json",
            ],
            cwd=REPO_ROOT,
            env=env,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_setup_builds_a_complete_private_vault_from_a_missing_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            private = root / "private"
            home = root / "home"
            home.mkdir()
            result = self.run_setup(private, home)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            for relative in (
                "AGENTS.md",
                "CLAUDE.md",
                "Home.md",
                "index.md",
                "log.md",
                "wiki.private.json",
                "README.md",
                "README-EN.md",
                "README-zh.md",
                "00_system/scripts/otw.py",
                "00_system/registry/private_scaffold_state.json",
            ):
                self.assertTrue((private / relative).exists(), relative)
            canonical_private = Path(payload["private_root"])
            self.assertIn(canonical_private.as_posix(), (private / "AGENTS.md").read_text(encoding="utf-8"))
            self.assertEqual(payload["sync"]["summary"]["conflict_staged"], 0)
            config = json.loads((home / ".obsidiantowiki.json").read_text(encoding="utf-8"))
            self.assertTrue(os.path.samefile(config["default_wiki_root"], private))

    def test_setup_migrates_exact_legacy_public_entry_but_preserves_custom_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            private = root / "private"
            home = root / "home"
            private.mkdir()
            home.mkdir()
            (private / "AGENTS.md").write_bytes((REPO_ROOT / "AGENTS.md").read_bytes())
            (private / "CLAUDE.md").write_text("# My private rules\n", encoding="utf-8")
            result = self.run_setup(private, home)
            self.assertEqual(result.returncode, 0, result.stderr)
            actions = {item["path"]: item["action"] for item in json.loads(result.stdout)["seed_actions"]}
            self.assertEqual(actions["AGENTS.md"], "legacy_migrated")
            self.assertEqual(actions["CLAUDE.md"], "conflict_staged")
            self.assertEqual((private / "CLAUDE.md").read_text(encoding="utf-8"), "# My private rules\n")
            self.assertTrue((private / "40_outputs/upgrade-candidates/private-scaffold/CLAUDE.md.new").exists())


if __name__ == "__main__":
    unittest.main()
