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
UPGRADER = REPO_ROOT / "00_system" / "scripts" / "project_scaffold.py"


class ProjectScaffoldUpgradeTests(unittest.TestCase):
    def test_attach_versions_core_bridge_without_installing_optional_adapters(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "project"
            vault = root / "vault"
            home = root / "home"
            repo.mkdir()
            vault.mkdir()
            home.mkdir()
            env = os.environ.copy()
            env.update({"HOME": str(home), "USERPROFILE": str(home), "PYTHONIOENCODING": "utf-8"})
            subprocess.run(["git", "init"], cwd=repo, env=env, check=True, capture_output=True)

            attached = subprocess.run(
                [sys.executable, str(OTW), "start", "--repo-root", str(repo), "--wiki-root", str(vault)],
                cwd=REPO_ROOT,
                env=env,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(attached.returncode, 0, attached.stderr)
            context = json.loads((repo / "wiki.context.json").read_text(encoding="utf-8"))
            self.assertEqual(Path(context["runtime_root"]), REPO_ROOT)
            self.assertEqual(context["project_scaffold_version"], 1)
            self.assertTrue((repo / ".obsidiantowiki/project-scaffold-state.json").exists())
            self.assertFalse((repo / "scripts/ai").exists())
            self.assertFalse((repo / ".agents").exists())
            candidate = repo / ".obsidiantowiki/upgrade-candidates/project-scaffold/docs/ai-workflows/AI_CODING_LIFECYCLE.md.new"
            self.assertFalse(candidate.exists(), "a newly generated lifecycle file must not conflict with its own template")

            agents = repo / "AGENTS.md"
            agents.write_text(agents.read_text(encoding="utf-8") + "\nUser-owned rule.\n", encoding="utf-8")
            lifecycle = repo / "docs/ai-workflows/AI_CODING_LIFECYCLE.md"
            lifecycle.write_text("# User lifecycle\n", encoding="utf-8")
            upgraded = subprocess.run(
                [sys.executable, str(UPGRADER), "--repo-root", str(repo), "--format", "json"],
                cwd=REPO_ROOT,
                env=env,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(upgraded.returncode, 0, upgraded.stderr)
            self.assertIn("User-owned rule.", agents.read_text(encoding="utf-8"))
            self.assertEqual(lifecycle.read_text(encoding="utf-8"), "# User lifecycle\n")
            self.assertTrue(candidate.exists())

            lifecycle.write_bytes(candidate.read_bytes())
            resolved = subprocess.run(
                [sys.executable, str(UPGRADER), "--repo-root", str(repo), "--format", "json"],
                cwd=REPO_ROOT,
                env=env,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(resolved.returncode, 0, resolved.stderr)
            self.assertFalse(candidate.exists(), "resolved managed candidates should not remain stale")

            tracked_paths = [
                repo / "AGENTS.md",
                repo / "CLAUDE.md",
                repo / "wiki.context.json",
                repo / ".obsidiantowiki/project-scaffold-state.json",
            ]
            before = {path: path.read_bytes() for path in tracked_paths}
            repeated = subprocess.run(
                [sys.executable, str(UPGRADER), "--repo-root", str(repo), "--format", "json"],
                cwd=REPO_ROOT,
                env=env,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(repeated.returncode, 0, repeated.stderr)
            report = json.loads(repeated.stdout)["reports"][0]
            self.assertEqual(report["status"], "current")
            self.assertTrue(all(item["action"] == "current" for item in report["actions"]))
            self.assertEqual(before, {path: path.read_bytes() for path in tracked_paths})


if __name__ == "__main__":
    unittest.main()
