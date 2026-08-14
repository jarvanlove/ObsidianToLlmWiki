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
    create_task_state,
    load_task_state,
    record_task_contract,
    transition_task,
)


class EngineeringGovernanceDiagnosisTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def complete_contract(self) -> dict[str, object]:
        return {
            "reproduction": "Submit an expired session token and observe HTTP 500.",
            "root_cause": "The expiry branch dereferences a missing account.",
            "minimal_fix": "Guard only the missing-account branch; no session schema or API changes.",
            "acceptance": ["Expired sessions return HTTP 401 without an exception."],
        }

    def test_bug_cannot_leave_investigation_when_any_required_fact_is_missing(self) -> None:
        missing_cases = ("reproduction", "root_cause", "minimal_fix", "acceptance")

        for missing in missing_cases:
            with self.subTest(missing=missing):
                create_task_state(self.repo, "Fix expired-session crash", "bug_fix")
                contract = self.complete_contract()
                contract[missing] = [] if missing == "acceptance" else None
                record_task_contract(self.repo, **contract)

                with self.assertRaisesRegex(ValueError, missing):
                    transition_task(self.repo, "planned")

                self.assertEqual(load_task_state(self.repo)["status"], "investigating")

    def test_complete_bug_contract_can_enter_implementation(self) -> None:
        create_task_state(self.repo, "Fix expired-session crash", "bug")
        state = record_task_contract(self.repo, **self.complete_contract())

        self.assertEqual(state["diagnosis"]["reproduction"]["status"], "reproduced")
        transition_task(self.repo, "planned", reason="root-cause contract complete")
        self.assertEqual(transition_task(self.repo, "implementing")["status"], "implementing")

    def test_explicit_not_reproduced_evidence_satisfies_the_reproduction_requirement(self) -> None:
        create_task_state(self.repo, "Fix intermittent export failure", "bug_fix")
        record_task_contract(
            self.repo,
            reproduction_unavailable_evidence="Three recorded traces show the upstream timeout; local replay cannot reach that service.",
            root_cause="The timeout is converted to a success result.",
            minimal_fix="Preserve the timeout as the existing typed failure.",
            acceptance=["Recorded timeout fixture returns the typed failure."],
        )

        self.assertEqual(transition_task(self.repo, "planned")["status"], "planned")

    def test_empty_not_reproduced_claim_does_not_bypass_the_gate(self) -> None:
        create_task_state(self.repo, "Fix intermittent export failure", "bug_fix")
        contract = self.complete_contract()
        contract.pop("reproduction")
        record_task_contract(self.repo, reproduction_unavailable_evidence="  ", **contract)

        with self.assertRaisesRegex(ValueError, "reproduction"):
            transition_task(self.repo, "planned")

    def test_feature_refactor_and_docs_do_not_require_a_bug_diagnosis(self) -> None:
        for intent in ("feature", "refactor", "docs"):
            with self.subTest(intent=intent):
                create_task_state(self.repo, f"Example {intent} task", intent)
                transition_task(self.repo, "planned")
                self.assertEqual(transition_task(self.repo, "implementing")["status"], "implementing")

    def test_project_lifecycle_documents_the_bug_only_gate(self) -> None:
        lifecycle = (REPO_ROOT / "docs/templates/project-control/AI_CODING_LIFECYCLE.md").read_text(encoding="utf-8")

        self.assertIn("Bug Root-Cause Gate", lifecycle)
        self.assertIn("reproduction steps or explicit evidence", lifecycle)
        self.assertIn("feature, refactor, or docs", lifecycle)


if __name__ == "__main__":
    unittest.main()
