from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "00_system" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from engineering_governance import (  # noqa: E402
    capture_git_baseline,
    compare_with_baseline,
    create_task_state,
    load_task_state,
    resume_summary,
    save_task_state,
)


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


class EngineeringGovernanceRecoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = Path(self.tempdir.name)
        git(self.repo, "init")
        git(self.repo, "config", "user.email", "test@example.com")
        git(self.repo, "config", "user.name", "Test")
        (self.repo / ".gitignore").write_text(".obsidiantowiki/\n", encoding="utf-8")
        (self.repo / "tracked.txt").write_text("original\n", encoding="utf-8")
        git(self.repo, "add", ".gitignore", "tracked.txt")
        git(self.repo, "commit", "-m", "initial")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_baseline_records_branch_head_tracked_untracked_and_time(self) -> None:
        (self.repo / "tracked.txt").write_text("preexisting\n", encoding="utf-8")
        (self.repo / "old-note.md").write_text("old\n", encoding="utf-8")

        baseline = capture_git_baseline(self.repo)

        self.assertTrue(baseline["is_git_repository"])
        self.assertEqual(baseline["branch"], git(self.repo, "branch", "--show-current").stdout.strip())
        self.assertEqual(baseline["head"], git(self.repo, "rev-parse", "HEAD").stdout.strip())
        self.assertEqual(baseline["tracked_modified"], ["tracked.txt"])
        self.assertEqual(baseline["untracked"], ["old-note.md"])
        self.assertTrue(baseline["captured_at"])
        self.assertEqual(set(baseline["path_hashes"]), {"old-note.md", "tracked.txt"})

    def test_compare_separates_preexisting_and_task_changes(self) -> None:
        (self.repo / "tracked.txt").write_text("preexisting\n", encoding="utf-8")
        (self.repo / "old-note.md").write_text("old\n", encoding="utf-8")
        baseline = capture_git_baseline(self.repo)
        (self.repo / "tracked.txt").write_text("changed again by task\n", encoding="utf-8")
        (self.repo / "feature.py").write_text("value = 1\n", encoding="utf-8")

        comparison = compare_with_baseline(self.repo, baseline)

        self.assertFalse(comparison["stale"])
        self.assertEqual(comparison["preexisting_changes"], ["old-note.md", "tracked.txt"])
        self.assertEqual(comparison["task_added"], ["feature.py"])
        self.assertEqual(comparison["task_touched_preexisting"], ["tracked.txt"])
        self.assertEqual(comparison["task_changes"], ["feature.py", "tracked.txt"])

    def test_baseline_keeps_staged_files_on_an_unborn_branch(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            git(repo, "init")
            (repo / "staged.txt").write_text("staged\n", encoding="utf-8")
            git(repo, "add", "staged.txt")

            baseline = capture_git_baseline(repo)

            self.assertEqual(baseline["head"], "")
            self.assertEqual(baseline["tracked_modified"], ["staged.txt"])

    def test_resume_marks_same_task_stale_when_head_changes(self) -> None:
        state = create_task_state(self.repo, "Implement feature", "code_change")
        state["baseline"] = capture_git_baseline(self.repo)
        save_task_state(self.repo, state)
        (self.repo / "external.txt").write_text("external\n", encoding="utf-8")
        git(self.repo, "add", "external.txt")
        git(self.repo, "commit", "-m", "external change")

        summary = resume_summary(self.repo)
        persisted = load_task_state(self.repo)

        self.assertEqual(summary["status"], "stale")
        self.assertIn("head_changed", summary["comparison"]["stale_reasons"])
        self.assertEqual(persisted["task_id"], state["task_id"])
        self.assertEqual(persisted["task"], state["task"])
        self.assertEqual(persisted["status"], "stale")

    def test_resume_marks_same_task_stale_when_branch_changes(self) -> None:
        state = create_task_state(self.repo, "Implement feature", "code_change")
        state["baseline"] = capture_git_baseline(self.repo)
        save_task_state(self.repo, state)
        git(self.repo, "switch", "-c", "external-branch")

        summary = resume_summary(self.repo)

        self.assertEqual(summary["status"], "stale")
        self.assertIn("branch_changed", summary["comparison"]["stale_reasons"])
        self.assertEqual(load_task_state(self.repo)["task_id"], state["task_id"])


if __name__ == "__main__":
    unittest.main()
