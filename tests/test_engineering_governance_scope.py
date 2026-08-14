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
    classify_risk,
    confirm_task_risk,
    create_task_state,
    evaluate_scope,
    load_task_state,
    record_acceptance_attempt,
    record_task_contract,
    save_task_state,
    set_task_risk,
    set_task_scope,
    transition_task,
)


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


class EngineeringGovernanceScopeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def new_task(self, task: str = "Refactor local formatter") -> None:
        create_task_state(self.repo, task, "code_change")
        set_task_risk(self.repo, classify_risk(task))

    def test_planned_files_are_allowed_to_continue(self) -> None:
        self.new_task()
        set_task_scope(self.repo, ["src/formatter.py", "tests/test_formatter.py"])

        result = evaluate_scope(self.repo, ["src/formatter.py", "tests/test_formatter.py"])

        self.assertEqual(result["drift"], [])
        self.assertEqual(result["action"], "continue")
        self.assertFalse(result["blocking"])

    def test_unplanned_changes_explain_each_scope_drift_category(self) -> None:
        self.new_task()
        set_task_scope(self.repo, ["src/formatter.py"])

        result = evaluate_scope(
            self.repo,
            [
                "new_area/module.py",
                "src/domain/model.py",
                "requirements.txt",
                "migrations/001_add_index.sql",
                "deploy/production.yaml",
            ],
        )

        reasons = {reason for item in result["drift"] for reason in item["reasons"]}
        self.assertIn("new_directory", reasons)
        self.assertIn("architecture_layer", reasons)
        self.assertIn("dependency_change", reasons)
        self.assertIn("database_migration", reasons)
        self.assertIn("deployment_configuration", reasons)

    def test_p3_drift_warns_without_blocking_but_p2_drift_blocks(self) -> None:
        cases = (
            ("Fix README spelling typo", "docs/readme-note.md", "warn", False, "investigating"),
            ("Refactor local formatter", "src/extra.py", "replan", True, "blocked"),
        )
        for task, changed, action, blocking, status in cases:
            with self.subTest(task=task):
                self.new_task(task)
                set_task_scope(self.repo, ["src/formatter.py"])
                result = evaluate_scope(self.repo, [changed])

                self.assertEqual(result["action"], action)
                self.assertEqual(result["blocking"], blocking)
                self.assertEqual(load_task_state(self.repo)["status"], status)

    def test_p1_and_p0_drift_clear_confirmation_and_require_reconfirmation(self) -> None:
        for task in ("Change authentication", "Delete production data"):
            with self.subTest(task=task):
                self.new_task(task)
                set_task_scope(self.repo, ["src/expected.py"])
                confirm_task_risk(self.repo, "product-owner")

                result = evaluate_scope(self.repo, ["src/unplanned.py"])
                state = load_task_state(self.repo)

                self.assertEqual(result["action"], "reconfirm")
                self.assertTrue(result["blocking"])
                self.assertEqual(state["status"], "blocked")
                self.assertIsNone(state["risk"]["confirmed_by"])

    def test_deployment_drift_promotes_a_low_risk_task_and_requires_confirmation(self) -> None:
        self.new_task("Fix README spelling typo")
        set_task_scope(self.repo, ["README.md"])

        result = evaluate_scope(self.repo, ["deploy/production.yaml"])
        state = load_task_state(self.repo)

        self.assertEqual(result["effective_level"], "P1")
        self.assertEqual(result["action"], "reconfirm")
        self.assertEqual(state["risk"]["level"], "P1")
        self.assertEqual(state["status"], "blocked")

    def test_scope_can_derive_task_changes_from_the_saved_git_baseline(self) -> None:
        git(self.repo, "init")
        git(self.repo, "config", "user.email", "test@example.com")
        git(self.repo, "config", "user.name", "Test")
        (self.repo / ".gitignore").write_text(".obsidiantowiki/\n", encoding="utf-8")
        (self.repo / "allowed.py").write_text("old\n", encoding="utf-8")
        git(self.repo, "add", ".gitignore", "allowed.py")
        git(self.repo, "commit", "-m", "initial")
        self.new_task()
        state = load_task_state(self.repo)
        state["baseline"] = capture_git_baseline(self.repo)
        save_task_state(self.repo, state)
        set_task_scope(self.repo, ["allowed.py"])
        (self.repo / "allowed.py").write_text("new\n", encoding="utf-8")
        (self.repo / "extra.py").write_text("extra\n", encoding="utf-8")

        result = evaluate_scope(self.repo)

        self.assertEqual(result["changed"], ["allowed.py", "extra.py"])
        self.assertEqual([item["path"] for item in result["drift"]], ["extra.py"])

    def test_scope_rejects_paths_outside_the_project(self) -> None:
        self.new_task()

        with self.assertRaisesRegex(ValueError, "escape the project"):
            set_task_scope(self.repo, ["../outside.txt"])
        with self.assertRaisesRegex(ValueError, "relative to the project"):
            evaluate_scope(self.repo, ["C:/outside.txt"])

    def test_third_distinct_failed_implementation_blocks_blind_patching(self) -> None:
        self.new_task()
        transition_task(self.repo, "planned")
        transition_task(self.repo, "implementing")

        first = record_acceptance_attempt(self.repo, "export-timeout", "patch-1", passed=False)
        repeated_command = record_acceptance_attempt(self.repo, "export-timeout", "patch-1", passed=False)
        second = record_acceptance_attempt(self.repo, "export-timeout", "patch-2", passed=False)
        third = record_acceptance_attempt(self.repo, "export-timeout", "patch-3", passed=False)

        self.assertEqual(first["failure_count"], 1)
        self.assertEqual(repeated_command["failure_count"], 1)
        self.assertEqual(second["failure_count"], 2)
        self.assertEqual(third["failure_count"], 3)
        self.assertEqual(third["status"], "blocked")
        self.assertTrue(third["recheck_required"])
        self.assertEqual(load_task_state(self.repo)["diagnosis"]["recheck_required"]["acceptance_id"], "export-timeout")
        with self.assertRaisesRegex(ValueError, "root-cause recheck"):
            record_acceptance_attempt(self.repo, "export-timeout", "patch-4", passed=False)

        record_task_contract(
            self.repo,
            root_cause="Revised diagnosis after the patch loop.",
            minimal_fix="A newly bounded fix based on the revised diagnosis.",
        )
        transition_task(self.repo, "investigating", reason="root cause rechecked")
        transition_task(self.repo, "planned")
        transition_task(self.repo, "implementing")
        after_recheck = record_acceptance_attempt(self.repo, "export-timeout", "patch-4", passed=False)
        self.assertEqual(after_recheck["failure_count"], 1)

    def test_a_pass_resets_the_consecutive_failure_count(self) -> None:
        self.new_task()
        transition_task(self.repo, "planned")
        transition_task(self.repo, "implementing")
        record_acceptance_attempt(self.repo, "export-timeout", "patch-1", passed=False)
        record_acceptance_attempt(self.repo, "export-timeout", "patch-2", passed=False)
        passed = record_acceptance_attempt(self.repo, "export-timeout", "patch-2", passed=True)
        after_pass = record_acceptance_attempt(self.repo, "export-timeout", "patch-3", passed=False)

        self.assertEqual(passed["failure_count"], 0)
        self.assertEqual(after_pass["failure_count"], 1)
        self.assertEqual(after_pass["status"], "implementing")


if __name__ == "__main__":
    unittest.main()
