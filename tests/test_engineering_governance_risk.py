from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "00_system" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from engineering_governance import (  # noqa: E402
    classify_risk,
    confirm_task_risk,
    create_task_state,
    set_task_risk,
    transition_task,
)


class EngineeringGovernanceRiskTests(unittest.TestCase):
    def test_classification_is_deterministic_and_explainable(self) -> None:
        cases = (
            ("Fix a spelling typo in README documentation", "P3"),
            ("Refactor a local date formatting helper", "P2"),
            ("Change authentication session validation", "P1"),
            ("Update role permissions", "P1"),
            ("Run a customer data migration", "P1"),
            ("Rotate an API secret", "P1"),
            ("Deploy the service", "P1"),
            ("Write the result to an external system", "P1"),
            ("Irreversibly delete archived records", "P0"),
            ("Modify production data directly", "P0"),
            ("Change a high-impact security boundary", "P0"),
        )

        for task, expected_level in cases:
            with self.subTest(task=task):
                result = classify_risk(task)
                self.assertEqual(result["level"], expected_level)
                self.assertEqual(result["source"], "deterministic-rule")
                self.assertTrue(result["reasons"])
                self.assertNotIn("score", result)

    def test_paths_and_intent_are_part_of_the_classification_evidence(self) -> None:
        result = classify_risk(
            "Update request handling",
            intent="code_change",
            paths=["src/authentication/session.py"],
        )

        self.assertEqual(result["level"], "P1")
        self.assertTrue(any("authentication" in reason for reason in result["reasons"]))

    def test_uncertainty_promotes_exactly_one_level_toward_p0(self) -> None:
        self.assertEqual(classify_risk("Fix README typo", uncertain=True)["level"], "P2")
        self.assertEqual(classify_risk("Refactor local helper", uncertain=True)["level"], "P1")
        self.assertEqual(classify_risk("Change login authentication", uncertain=True)["level"], "P0")
        self.assertEqual(classify_risk("Delete production data", uncertain=True)["level"], "P0")

    def test_p1_and_p0_require_responsibility_confirmation_before_implementation(self) -> None:
        for task in ("Change authentication", "Delete production data"):
            with self.subTest(task=task), tempfile.TemporaryDirectory() as directory:
                repo = Path(directory)
                create_task_state(repo, task, "code_change")
                set_task_risk(repo, classify_risk(task))
                transition_task(repo, "planned", reason="scope recorded")

                with self.assertRaisesRegex(ValueError, "responsibility confirmation"):
                    transition_task(repo, "implementing")

                confirmed = confirm_task_risk(repo, "product-owner")
                self.assertEqual(confirmed["risk"]["confirmed_by"], "product-owner")
                self.assertTrue(confirmed["risk"]["confirmed_at"])
                self.assertEqual(transition_task(repo, "implementing")["status"], "implementing")

    def test_p2_can_enter_implementation_without_high_risk_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            create_task_state(repo, "Refactor local helper", "code_change")
            set_task_risk(repo, classify_risk("Refactor local helper"))
            transition_task(repo, "planned", reason="scope recorded")

            self.assertEqual(transition_task(repo, "implementing")["status"], "implementing")


if __name__ == "__main__":
    unittest.main()
