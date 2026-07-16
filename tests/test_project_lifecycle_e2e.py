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


class ProjectLifecycleE2ETests(unittest.TestCase):
    def test_natural_language_lifecycle_bootstraps_and_closes_disposable_project(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "sample-project"
            vault = root / "private-wiki"
            home = root / "home"
            repo.mkdir()
            vault.mkdir()
            home.mkdir()
            env = os.environ.copy()
            env["HOME"] = str(home)
            env["USERPROFILE"] = str(home)
            env["PYTHONIOENCODING"] = "utf-8"
            for command in (
                ["git", "init"],
                ["git", "config", "user.email", "test@example.com"],
                ["git", "config", "user.name", "Test"],
            ):
                result = subprocess.run(command, cwd=repo, env=env, check=False, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)

            started = subprocess.run(
                [sys.executable, str(OTW), "start", "--repo-root", str(repo), "--wiki-root", str(vault)],
                cwd=REPO_ROOT,
                env=env,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(started.returncode, 0, started.stderr)
            context = json.loads((repo / "wiki.context.json").read_text(encoding="utf-8"))
            self.assertEqual(Path(context["wiki_root"]), vault.resolve())
            for name in ("PRODUCT_SPEC.md", "ARCHITECTURE.md", "TASKS.md", "TESTING.md", "AGENTS.md", "CLAUDE.md"):
                self.assertTrue((repo / name).exists(), name)
            for path in (
                vault / "00_system" / "scripts" / "otw.py",
                vault / "00_system" / "registry" / "vault_schema.json",
                vault / "00_system" / "registry" / "private_scaffold_state.json",
                vault / "AGENTS.md",
                vault / "wiki.private.json",
                vault / context["project_index"],
                vault / context["project_memory"],
            ):
                self.assertTrue(path.exists(), str(path))
            bridge = (repo / "AGENTS.md").read_text(encoding="utf-8")
            self.assertNotIn(str(vault), bridge)
            ignored = subprocess.run(
                ["git", "check-ignore", "wiki.context.json"],
                cwd=repo,
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(ignored.returncode, 0, ignored.stderr)

            upgraded = subprocess.run(
                [sys.executable, str(OTW), "upgrade", "--repo-root", str(repo), "--wiki-root", str(vault), "--apply"],
                cwd=REPO_ROOT,
                env=env,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(upgraded.returncode, 0, upgraded.stderr)
            self.assertFalse((repo / ".agents").exists(), "normal upgrade must not install opt-in project adapters")

            continued = subprocess.run(
                [sys.executable, str(OTW), "continue", "--repo-root", str(repo)],
                cwd=REPO_ROOT,
                env=env,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(continued.returncode, 0, continued.stderr)

            closed = subprocess.run(
                [sys.executable, str(OTW), "close", "--repo-root", str(repo), "--verification", "E2E passed"],
                cwd=REPO_ROOT,
                env=env,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(closed.returncode, 0, closed.stderr)
            receipt_path = repo / ".obsidiantowiki" / "session-receipt.json"
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            resolve = [sys.executable, str(OTW), "resolve", "--repo-root", str(repo), "--strict"]
            for candidate in receipt["candidates"]:
                resolve.extend(["--resolution", f"{candidate['id']}=not_applicable"])
            resolved = subprocess.run(
                resolve,
                cwd=REPO_ROOT,
                env=env,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(resolved.returncode, 0, resolved.stderr)
            self.assertEqual(json.loads(receipt_path.read_text(encoding="utf-8"))["status"], "resolved")


if __name__ == "__main__":
    unittest.main()
