from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
OTW = REPO_ROOT / "00_system" / "scripts" / "otw.py"
sys.path.insert(0, str(REPO_ROOT / "00_system" / "scripts"))

from handle_nl_request import classify_request  # noqa: E402


class RuntimeSetupTests(unittest.TestCase):
    def test_natural_language_routes_setup_apply_update_and_check_only(self) -> None:
        self.assertEqual(classify_request("安装并初始化 ObsidianToWiki"), "setup_runtime")
        self.assertEqual(classify_request("更新 ObsidianToWiki"), "update_runtime")
        self.assertEqual(
            classify_request("检查 ObsidianToWiki 是否有更新，不要应用"),
            "check_update_runtime",
        )

    def test_setup_is_one_command_and_uses_isolated_provider_home(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            private = root / "private"
            home = root / "home"
            home.mkdir()
            env = os.environ.copy()
            env.update({"HOME": str(home), "USERPROFILE": str(home), "PYTHONIOENCODING": "utf-8"})
            result = subprocess.run(
                [
                    sys.executable,
                    str(OTW),
                    "setup",
                    "--private-root",
                    str(private),
                    "--provider",
                    "agents",
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
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "complete")
            self.assertEqual(payload["runtime_version"], "2.0.0")
            self.assertTrue((private / "00_system/registry/runtime_update_receipt.json").exists())
            self.assertTrue((home / ".agents/skills/obsidiantowiki-manager/SKILL.md").exists())
            self.assertFalse((home / ".claude/skills/obsidiantowiki-manager/SKILL.md").exists())


if __name__ == "__main__":
    unittest.main()
