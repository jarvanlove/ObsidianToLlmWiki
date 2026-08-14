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
            self.assertNotIn("请手动", started.stdout)
            context = json.loads((repo / "wiki.context.json").read_text(encoding="utf-8"))
            self.assertEqual(Path(context["wiki_root"]), vault.resolve())
            self.assertEqual(context["project_scaffold_version"], 4)
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

            evidence = json.dumps({
                "kind": "test",
                "command": "python -m unittest tests.test_project_lifecycle_e2e -v",
                "exit_code": 0,
                "result": "passed",
                "recorded_at": "2026-08-14T11:00:00+08:00",
                "source": "deterministic",
            })
            closed = subprocess.run(
                [sys.executable, str(OTW), "close", "--repo-root", str(repo), "--evidence", evidence],
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
            self.assertTrue(receipt["knowledge_candidates"])
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
            resolved_receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(resolved_receipt["status"], "resolved")
            self.assertEqual(resolved_receipt["memory_status"], "pending_memory_repair")
            task_state = json.loads((repo / ".obsidiantowiki" / "task-state.json").read_text(encoding="utf-8"))
            self.assertEqual(task_state["task_id"], resolved_receipt["task_id"])


if __name__ == "__main__":
    unittest.main()
