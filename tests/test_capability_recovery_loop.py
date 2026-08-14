from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "00_system" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from engineering_governance import (  # noqa: E402
    assess_capability_intervention,
    create_task_state,
    load_task_state,
    plan_capability_intervention,
    record_capability_observation,
    set_task_risk,
)
from memory_compiler import compile_receipt  # noqa: E402
from project_session import (  # noqa: E402
    build_receipt,
    confirm_receipt_understanding,
    resolve_receipt,
    write_json_atomic,
)


def passing_evidence() -> list[dict[str, object]]:
    return [
        {
            "kind": "test",
            "command": "python -m unittest tests.test_capability_recovery_loop -v",
            "exit_code": 0,
            "result": "passed",
            "recorded_at": datetime.now().astimezone().replace(microsecond=0).isoformat(),
            "source": "deterministic",
        }
    ]


def close_report(repo: Path, *, risk: str = "P2") -> dict[str, object]:
    state = load_task_state(repo)
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


class CapabilityRecoveryLoopTests(unittest.TestCase):
    def test_intervention_is_quiet_without_a_signal_and_uses_only_five_triggers(self) -> None:
        quiet = assess_capability_intervention()
        cases = (
            {"new_concept": True},
            {"risk_level": "P1"},
            {"repeated_module_issues": 2},
            {"ai_misjudgment": True},
            {"consecutive_understanding_skips": 2},
        )

        self.assertFalse(quiet["triggered"])
        self.assertEqual(quiet["options"], [])
        for signals in cases:
            with self.subTest(signals=signals):
                result = assess_capability_intervention(**signals)
                self.assertTrue(result["triggered"])
                self.assertEqual(
                    [item["id"] for item in result["options"]],
                    ["root_cause_first", "explain_call_chain", "skip_learning"],
                )
                self.assertNotIn("score", json.dumps(result, ensure_ascii=False).lower())

    def test_intervention_is_offered_at_most_once_per_task(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            create_task_state(repo, "Change authentication", "code_change")

            first = plan_capability_intervention(repo, topic="authentication/session", new_concept=True)
            second = plan_capability_intervention(repo, topic="authentication/session", ai_misjudgment=True)
            saved = load_task_state(repo)["capability_recovery"]

        self.assertEqual(first["status"], "offered")
        self.assertEqual(second["status"], "already_offered")
        self.assertEqual(second["intervention_id"], first["intervention_id"])
        self.assertEqual(saved["intervention"]["intervention_id"], first["intervention_id"])

    def test_observation_is_structured_safe_idempotent_and_never_shared(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            create_task_state(repo, "Change authentication", "code_change")

            candidate = record_capability_observation(
                repo,
                topic="authentication/session boundary",
                observation_kind="rollback_point_identified",
                observation="User identified password=top-secret rollback at C:\\private\\service before reveal.",
                evidence_ref="session-receipt.json#evidence-3",
            )
            duplicate = record_capability_observation(
                repo,
                topic="authentication/session boundary",
                observation_kind="rollback_point_identified",
                observation="User identified password=top-secret rollback at C:\\private\\service before reveal.",
                evidence_ref="session-receipt.json#evidence-3",
            )
            stored = [
                item
                for item in load_task_state(repo)["knowledge_candidates"]
                if item.get("kind") == "capability_observation"
            ]
            with self.assertRaisesRegex(ValueError, "shared"):
                record_capability_observation(
                    repo,
                    topic="authentication/session boundary",
                    observation_kind="rollback_point_identified",
                    observation="User identified the rollback point.",
                    evidence_ref="session-receipt.json#evidence-3",
                    suggested_destination="shared",
                )
            with self.assertRaisesRegex(ValueError, "sensitive"):
                record_capability_observation(
                    repo,
                    topic="authentication/session boundary",
                    observation_kind="rollback_point_identified",
                    observation="User identified the rollback point.",
                    evidence_ref="session-receipt.json#evidence-3",
                    sensitive=True,
                )

        self.assertEqual(candidate, duplicate)
        self.assertEqual(len(stored), 1)
        self.assertEqual(candidate["type"], "capability_observation")
        self.assertEqual(candidate["observation_kind"], "rollback_point_identified")
        self.assertEqual(candidate["destination"], "personal")
        self.assertEqual(candidate["suggested_destination"], "personal_memory")
        self.assertEqual(candidate["status"], "pending")
        self.assertFalse(candidate["sensitive"])
        rendered = json.dumps(candidate, ensure_ascii=False)
        self.assertNotIn("top-secret", rendered)
        self.assertNotIn("C:\\private", rendered)

    def test_observation_requires_an_allowed_event_and_auditable_evidence_reference(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            create_task_state(repo, "Change authentication", "code_change")

            with self.assertRaisesRegex(ValueError, "observation kind"):
                record_capability_observation(
                    repo,
                    topic="authentication/session boundary",
                    observation_kind="overall_skill_score",
                    observation="User is an expert.",
                    evidence_ref="session-receipt.json#evidence-3",
                )
            with self.assertRaisesRegex(ValueError, "evidence reference"):
                record_capability_observation(
                    repo,
                    topic="authentication/session boundary",
                    observation_kind="rollback_point_identified",
                    observation="User identified the rollback point.",
                    evidence_ref="trust me",
                )

    def test_candidate_waits_for_receipt_resolution_and_compiles_as_pending_review(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            vault = root / "vault"
            repo.mkdir()
            vault.mkdir()
            create_task_state(repo, "Change authentication", "code_change")
            record_capability_observation(
                repo,
                topic="authentication/session boundary",
                observation_kind="root_cause_proposed",
                observation="User proposed the session cache as the failure boundary before reveal.",
                evidence_ref="session-receipt.json#evidence-0",
            )
            receipt = build_receipt(repo, close_report(repo))
            receipt_path = root / "session-receipt.json"
            write_json_atomic(receipt_path, receipt)

            blocked = compile_receipt(
                receipt_path,
                wiki_root=vault,
                project_slug="demo",
                today=date(2026, 8, 14),
            )
            resolved = resolve_receipt(receipt_path, [])
            compiled = compile_receipt(
                receipt_path,
                wiki_root=vault,
                project_slug="demo",
                today=date(2026, 8, 14),
            )

        capability = next(
            item for item in receipt["knowledge_candidates"] if item["kind"] == "capability_observation"
        )
        self.assertEqual(capability["status"], "pending")
        self.assertEqual(blocked["status"], "blocked")
        self.assertEqual(resolved["status"], "resolved")
        self.assertEqual(compiled["cards"][0]["status"], "pending_review")
        self.assertFalse((vault / "10_personal").exists())
        self.assertFalse((vault / "30_shared").exists())

    def test_p1_candidate_appears_only_after_real_human_understanding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            create_task_state(repo, "Change authentication", "code_change")
            set_task_risk(
                repo,
                {"level": "P1", "reasons": ["authentication boundary"], "source": "deterministic-rule"},
            )
            record_capability_observation(
                repo,
                topic="authentication/session boundary",
                observation_kind="risk_boundary_identified",
                observation="User identified the authentication boundary before reveal.",
                evidence_ref="session-receipt.json#evidence-0",
            )
            receipt = build_receipt(repo, close_report(repo, risk="P1"))
            path = repo / "receipt.json"
            write_json_atomic(path, receipt)

            confirmed = confirm_receipt_understanding(
                repo,
                path,
                confirmed_by="product-owner",
                understood_impact_and_remaining_risks=True,
                confirmation_source="human",
            )

        self.assertFalse(
            any(item["kind"] == "capability_observation" for item in receipt["knowledge_candidates"])
        )
        self.assertTrue(
            any(item["kind"] == "capability_observation" for item in confirmed["knowledge_candidates"])
        )


if __name__ == "__main__":
    unittest.main()
