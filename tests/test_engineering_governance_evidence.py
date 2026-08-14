from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "00_system" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from project_session import build_receipt, load_receipt, parse_evidence_inputs  # noqa: E402


def evidence(*, source: str = "deterministic", exit_code: int = 0, result: str = "passed") -> dict[str, object]:
    return {
        "kind": "test",
        "command": "python -m unittest tests.test_example -v",
        "exit_code": exit_code,
        "result": result,
        "recorded_at": "2026-08-14T11:00:00+08:00",
        "source": source,
    }


def report(*, risk: str = "P2", items: list[dict[str, object]] | None = None, verification: str = "") -> dict[str, object]:
    return {
        "task": "Require structured evidence",
        "task_id": "task-evidence",
        "risk": {"level": risk},
        "verification": verification,
        "evidence": items or [],
        "changed_files": ["feature.py"],
        "control_file_update_candidates": [],
        "wiki_file_back_candidates": [],
    }


class EngineeringGovernanceEvidenceTests(unittest.TestCase):
    def test_structured_evidence_has_required_fields_and_passes(self) -> None:
        receipt = build_receipt(REPO_ROOT, report(items=[evidence()]))

        self.assertEqual(receipt["schema_version"], 2)
        self.assertEqual(receipt["status"], "pending")
        self.assertEqual(
            set(receipt["evidence"][0]),
            {"kind", "command", "exit_code", "result", "recorded_at", "source"},
        )
        self.assertEqual(receipt["gate_results"]["verification_evidence"]["status"], "passed")
        self.assertEqual(receipt["explanation_package"], {})

    def test_powershell_seven_digit_iso_timestamp_passes(self) -> None:
        item = evidence()
        item["recorded_at"] = "2026-08-14T11:35:48.1508662+08:00"

        receipt = build_receipt(REPO_ROOT, report(items=[item]))

        self.assertEqual(receipt["status"], "pending")
        self.assertEqual(receipt["gate_results"]["verification_evidence"]["status"], "passed")

    def test_malformed_timestamp_remains_blocked(self) -> None:
        item = evidence()
        item["recorded_at"] = "2026-08-14-not-a-time"

        receipt = build_receipt(REPO_ROOT, report(items=[item]))

        self.assertEqual(receipt["status"], "blocked")
        self.assertIn(
            "evidence_0_invalid_recorded_at",
            receipt["gate_results"]["verification_evidence"]["reasons"],
        )

    def test_plain_verification_string_cannot_close(self) -> None:
        receipt = build_receipt(REPO_ROOT, report(verification="测试通过"))

        self.assertEqual(receipt["status"], "blocked")
        self.assertIn("legacy_unstructured", receipt["gate_results"]["verification_evidence"]["reasons"])
        self.assertNotIn("task-evidence", {item["stable_key"] for item in receipt["knowledge_candidates"]})

    def test_nonzero_exit_code_cannot_be_marked_passed(self) -> None:
        receipt = build_receipt(REPO_ROOT, report(items=[evidence(exit_code=1)]))

        self.assertEqual(receipt["status"], "blocked")
        self.assertIn("passed_evidence_has_nonzero_exit_code", receipt["gate_results"]["verification_evidence"]["reasons"])

    def test_missing_fields_are_rejected(self) -> None:
        incomplete = evidence()
        del incomplete["command"]

        receipt = build_receipt(REPO_ROOT, report(items=[incomplete]))

        reasons = receipt["gate_results"]["verification_evidence"]["reasons"]
        self.assertEqual(receipt["status"], "blocked")
        self.assertIn("evidence_0_missing_fields:command", reasons)

    def test_unknown_source_is_rejected(self) -> None:
        receipt = build_receipt(REPO_ROOT, report(items=[evidence(source="model_guess")]))

        self.assertEqual(receipt["status"], "blocked")
        self.assertIn("evidence_0_invalid_source", receipt["gate_results"]["verification_evidence"]["reasons"])

    def test_high_risk_ai_self_check_requires_independent_evidence(self) -> None:
        receipt = build_receipt(REPO_ROOT, report(risk="P1", items=[evidence(source="ai_self_check")]))

        self.assertEqual(receipt["status"], "blocked")
        self.assertIn("independent_evidence_required", receipt["gate_results"]["verification_evidence"]["reasons"])

    def test_v1_receipt_is_read_as_legacy_unstructured_v2(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "receipt.json"
            path.write_text(
                json.dumps({"schema_version": 1, "status": "resolved", "verification": "tests passed"}),
                encoding="utf-8",
            )

            receipt = load_receipt(path)

        self.assertEqual(receipt["schema_version"], 2)
        self.assertEqual(receipt["legacy_schema_version"], 1)
        self.assertEqual(receipt["status"], "blocked")
        self.assertEqual(receipt["evidence"], [])
        self.assertIn("legacy_unstructured", receipt["gate_results"]["verification_evidence"]["reasons"])

    def test_evidence_file_accepts_a_bounded_evidence_list(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "evidence.json"
            path.write_text(json.dumps({"evidence": [evidence()]}), encoding="utf-8")

            items = parse_evidence_inputs(root, [], "evidence.json")

        self.assertEqual(items, [evidence()])

    def test_evidence_count_is_bounded(self) -> None:
        with self.assertRaisesRegex(ValueError, "limited to 50"):
            parse_evidence_inputs(REPO_ROOT, [json.dumps(evidence())] * 51)


if __name__ == "__main__":
    unittest.main()
