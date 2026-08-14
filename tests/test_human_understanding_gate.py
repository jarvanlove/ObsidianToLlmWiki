from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "00_system" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from engineering_governance import (  # noqa: E402
    EXPLANATION_FIELDS,
    build_explanation_package,
    classify_risk,
    create_task_state,
    evaluate_understanding_gate,
    load_task_state,
    record_human_understanding,
    record_task_contract,
    set_task_risk,
    transition_task,
)
from project_session import (  # noqa: E402
    build_receipt,
    confirm_receipt_understanding,
    finalize_memory_maintenance,
    resolve_receipt,
    write_json_atomic,
)


def passing_evidence() -> list[dict[str, object]]:
    return [
        {
            "kind": "unit_tests",
            "command": "python -m unittest --token=do-not-copy",
            "exit_code": 0,
            "result": "passed",
            "recorded_at": datetime.now().astimezone().replace(microsecond=0).isoformat(),
            "source": "deterministic",
        }
    ]


def close_report(repo: Path, *, risk: str) -> dict[str, object]:
    state = create_task_state(repo, "Change authentication session validation", "code_change")
    set_task_risk(
        repo,
        {
            "level": risk,
            "reasons": ["test risk boundary"],
            "source": "deterministic-rule",
        },
    )
    return {
        "task": state["task"],
        "task_id": state["task_id"],
        "risk": {"level": risk},
        "verification": "",
        "evidence": passing_evidence(),
        "changed_files": ["src/auth/session.py"],
        "control_file_update_candidates": [],
        "wiki_file_back_candidates": [],
    }


class HumanUnderstandingGateTests(unittest.TestCase):
    def test_explanation_package_has_all_seven_safe_fields(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            create_task_state(repo, "Fix authentication failure at C:\\private\\service", "bug_fix")
            set_task_risk(repo, classify_risk("Fix authentication failure"))
            record_task_contract(
                repo,
                reproduction="Expired session fails.",
                root_cause="password=super-secret is copied into the failure branch.",
                minimal_fix="Remove only that copy.",
                acceptance=["Expired sessions return 401."],
            )

            package = build_explanation_package(
                repo,
                changed_files=["src/auth/session.py"],
                evidence=passing_evidence(),
                risk_level="P1",
            )

        self.assertEqual(tuple(package), EXPLANATION_FIELDS)
        self.assertTrue(all(package[field] for field in EXPLANATION_FIELDS))
        rendered = str(package)
        self.assertNotIn("super-secret", rendered)
        self.assertNotIn("do-not-copy", rendered)
        self.assertNotIn("C:\\private", rendered)
        self.assertEqual(package["data_or_call_chain_changes"], "unknown")

    def test_p3_auto_passes_and_p2_displays_without_confirmation(self) -> None:
        for level, action in (("P3", "auto_pass"), ("P2", "display")):
            with self.subTest(level=level), tempfile.TemporaryDirectory() as directory:
                repo = Path(directory)
                create_task_state(repo, "Example task", "code_change")
                set_task_risk(
                    repo,
                    {"level": level, "reasons": ["test boundary"], "source": "deterministic-rule"},
                )
                package = build_explanation_package(repo, changed_files=["example.py"], evidence=[])

                gate = evaluate_understanding_gate(repo, package, risk_level=level)

                self.assertEqual(gate["status"], "passed")
                self.assertEqual(gate["action"], action)
                self.assertFalse(gate["human_confirmation_required"])

    def test_p1_requires_current_human_confirmation_and_rejects_ai_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            create_task_state(repo, "Change authentication", "code_change")
            set_task_risk(repo, classify_risk("Change authentication"))
            package = build_explanation_package(repo, changed_files=["src/auth.py"], evidence=passing_evidence())

            blocked = evaluate_understanding_gate(repo, package, risk_level="P1")
            with self.assertRaisesRegex(ValueError, "human confirmation source"):
                record_human_understanding(
                    repo,
                    package,
                    confirmed_by="AI agent",
                    understood_impact_and_remaining_risks=True,
                    confirmation_source="ai_self_check",
                )
            record_human_understanding(
                repo,
                package,
                confirmed_by="product-owner",
                understood_impact_and_remaining_risks=True,
                confirmation_source="human",
            )
            passed = evaluate_understanding_gate(repo, package, risk_level="P1")
            stale_package = {**package, "remaining_risks": "A newly discovered risk."}
            stale = evaluate_understanding_gate(repo, stale_package, risk_level="P1")

        self.assertEqual(blocked["status"], "blocked")
        self.assertIn("human_understanding_confirmation_required", blocked["reasons"])
        self.assertEqual(passed["status"], "passed")
        self.assertEqual(passed["confirmed_by"], "product-owner")
        self.assertIn("explanation_package_changed", stale["reasons"])

    def test_p0_requires_both_understanding_and_explicit_authorization(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            create_task_state(repo, "Delete production data", "code_change")
            set_task_risk(repo, classify_risk("Delete production data"))
            package = build_explanation_package(repo, changed_files=["ops/delete.py"], evidence=passing_evidence())
            record_human_understanding(
                repo,
                package,
                confirmed_by="product-owner",
                understood_impact_and_remaining_risks=True,
                confirmation_source="human",
            )

            blocked = evaluate_understanding_gate(repo, package, risk_level="P0")
            record_human_understanding(
                repo,
                package,
                confirmed_by="product-owner",
                understood_impact_and_remaining_risks=True,
                explicit_authorization=True,
                confirmation_source="human",
            )
            passed = evaluate_understanding_gate(repo, package, risk_level="P0")

        self.assertIn("explicit_authorization_required", blocked["reasons"])
        self.assertEqual(passed["status"], "passed")
        self.assertTrue(passed["explicit_authorization"])

    def test_p1_receipt_cannot_resolve_until_human_confirms_its_package(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            report = close_report(repo, risk="P1")
            receipt = build_receipt(repo, report)
            path = repo / "receipt.json"
            write_json_atomic(path, receipt)

            with self.assertRaisesRegex(SystemExit, "human understanding gate"):
                resolve_receipt(path, [])
            confirmed = confirm_receipt_understanding(
                repo,
                path,
                confirmed_by="product-owner",
                understood_impact_and_remaining_risks=True,
                confirmation_source="human",
            )
            resolved = resolve_receipt(path, [])

        self.assertEqual(receipt["status"], "blocked")
        self.assertEqual(receipt["gate_results"]["human_understanding"]["status"], "blocked")
        self.assertEqual(confirmed["status"], "pending")
        self.assertIn(
            report["task_id"],
            {item["stable_key"] for item in confirmed["knowledge_candidates"]},
        )
        self.assertEqual(resolved["status"], "resolved")

    def test_unified_runtime_forwards_human_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            receipt = build_receipt(repo, close_report(repo, risk="P1"))
            path = repo / ".obsidiantowiki" / "session-receipt.json"
            write_json_atomic(path, receipt)

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "otw.py"),
                    "understand",
                    "--repo-root",
                    str(repo),
                    "--confirmed-by",
                    "product-owner",
                    "--understood-impact-and-risks",
                    "--confirmation-source",
                    "human",
                ],
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("Session receipt: pending", completed.stdout)

    def test_resolved_p2_receipt_closes_the_matching_governed_task(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            report = close_report(repo, risk="P2")
            transition_task(repo, "planned", reason="test plan")
            transition_task(repo, "implementing", reason="test implementation")
            transition_task(repo, "verifying", reason="test verification")
            path = repo / "receipt.json"
            write_json_atomic(path, build_receipt(repo, report))

            receipt = resolve_receipt(path, [])
            finalized = finalize_memory_maintenance(repo, path, receipt)

            self.assertEqual(finalized["governance_status"], "closed")
            self.assertEqual(load_task_state(repo)["status"], "closed")


if __name__ == "__main__":
    unittest.main()
