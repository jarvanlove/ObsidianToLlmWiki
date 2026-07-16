from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "00_system" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from runtime_manager import apply_update, inspect_git_update  # noqa: E402


def git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


class RuntimeUpdateTests(unittest.TestCase):
    def test_update_check_detects_fast_forward_and_dirty_preflight_blocks_apply(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            remote = root / "origin.git"
            seed = root / "seed"
            user = root / "user"
            git(root, "init", "--bare", str(remote))
            git(root, "clone", str(remote), str(seed))
            git(seed, "config", "user.email", "test@example.com")
            git(seed, "config", "user.name", "Test")
            (seed / "release.txt").write_text("one\n", encoding="utf-8")
            git(seed, "add", "release.txt")
            git(seed, "commit", "-m", "one")
            git(seed, "push", "-u", "origin", "HEAD:main")
            git(remote, "symbolic-ref", "HEAD", "refs/heads/main")
            git(root, "clone", str(remote), str(user))

            current = inspect_git_update(user, fetch=True)
            self.assertFalse(current["update_available"])
            (seed / "release.txt").write_text("two\n", encoding="utf-8")
            git(seed, "add", "release.txt")
            git(seed, "commit", "-m", "two")
            git(seed, "push", "origin", "HEAD:main")
            available = inspect_git_update(user, fetch=True)
            self.assertTrue(available["update_available"])
            self.assertTrue(available["fast_forward"])

            (user / "local.txt").write_text("dirty\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "uncommitted changes"):
                apply_update(user, root / "private", "agents")


if __name__ == "__main__":
    unittest.main()
