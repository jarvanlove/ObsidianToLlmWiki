from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "00_system" / "scripts" / "install_manager_skill.py"


class ManagerSkillInstallTests(unittest.TestCase):
    def test_install_is_repeatable_and_preserves_user_customization(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            agents_root = root / "agents"
            claude_root = root / "claude"
            command = [
                sys.executable,
                str(SCRIPT),
                "--provider",
                "all",
                "--agents-root",
                str(agents_root),
                "--claude-root",
                str(claude_root),
                "--format",
                "json",
            ]
            first = subprocess.run(command, check=False, capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual([item["action"] for item in json.loads(first.stdout)["results"]], ["installed", "installed"])

            agents_skill = agents_root / "obsidiantowiki-manager" / "SKILL.md"
            claude_skill = claude_root / "obsidiantowiki-manager" / "SKILL.md"
            self.assertIn(REPO_ROOT.as_posix(), agents_skill.read_text(encoding="utf-8"))
            self.assertTrue(claude_skill.exists())

            agents_skill.write_text("# User customized manager\n", encoding="utf-8")
            second = subprocess.run(command, check=False, capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(second.returncode, 0, second.stderr)
            actions = [item["action"] for item in json.loads(second.stdout)["results"]]
            self.assertEqual(actions, ["conflict_staged", "current"])
            self.assertEqual(agents_skill.read_text(encoding="utf-8"), "# User customized manager\n")
            self.assertTrue((agents_skill.parent / "SKILL.md.new").exists())


if __name__ == "__main__":
    unittest.main()
