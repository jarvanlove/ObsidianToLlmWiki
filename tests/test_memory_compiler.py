from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "00_system" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from memory_compiler import compile_receipt  # noqa: E402
from context_integrity import inspect_page, load_memory_policy  # noqa: E402
from project_session import build_receipt  # noqa: E402
from wiki_lib import parse_frontmatter  # noqa: E402


class MemoryCompilerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.vault = self.root / "vault"
        self.receipts = self.root / "receipts"
        self.vault.mkdir()
        self.receipts.mkdir()
        self.policy = REPO_ROOT / "00_system" / "registry" / "memory_policy.json"

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def write_receipt(
        self,
        name: str,
        candidates: list[dict[str, object]],
        *,
        status: str = "resolved",
        risk: str = "P2",
        verification: str = "python -m unittest: passed",
    ) -> Path:
        path = self.receipts / f"{name}.json"
        path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "status": status,
                    "task_id": name,
                    "risk": {"level": risk},
                    "verification": verification,
                    "knowledge_candidates": candidates,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return path

    def compile(self, receipt: Path) -> dict[str, object]:
        return compile_receipt(
            receipt,
            wiki_root=self.vault,
            project_slug="demo",
            policy_path=self.policy,
            today=date(2026, 8, 13),
        )

    def card_files(self) -> list[Path]:
        return sorted((self.vault / "20_projects" / "active" / "demo" / "memory").glob("*.md"))

    @staticmethod
    def candidate(kind: str, key: str, summary: str, **extra: object) -> dict[str, object]:
        value: dict[str, object] = {
            "kind": kind,
            "stable_key": key,
            "summary": summary,
            "evidence_refs": ["git:abc123"],
            "destination": "project",
        }
        value.update(extra)
        return value

    def read_card(self, path: Path) -> tuple[dict[str, object], str]:
        return parse_frontmatter(path.read_text(encoding="utf-8"))

    def test_only_resolved_evidence_backed_receipts_can_compile(self) -> None:
        pending = self.write_receipt(
            "pending-task",
            [self.candidate("decision", "retry-policy", "Use bounded retries.")],
            status="pending",
        )
        missing_evidence = self.write_receipt(
            "missing-evidence",
            [self.candidate("decision", "retry-policy", "Use bounded retries.")],
            verification="",
        )

        self.assertEqual(self.compile(pending)["status"], "blocked")
        self.assertEqual(self.compile(missing_evidence)["status"], "blocked")
        self.assertEqual(self.card_files(), [])

    def test_routine_receipt_without_candidates_creates_no_cards(self) -> None:
        result = self.compile(self.write_receipt("routine-task", []))

        self.assertEqual(result["status"], "no_candidates")
        self.assertEqual(self.card_files(), [])

    def test_new_session_receipt_has_task_identity_and_automatic_milestone_candidate(self) -> None:
        report = {
            "task": "Implement bounded memory",
            "verification": "tests passed",
            "changed_files": ["memory.py"],
            "control_file_update_candidates": [],
            "wiki_file_back_candidates": [],
        }

        receipt = build_receipt(self.root, report)

        self.assertTrue(str(receipt["task_id"]).startswith("session-"))
        self.assertEqual(receipt["task"], report["task"])
        self.assertEqual(receipt["knowledge_candidates"][0]["kind"], "milestone")
        self.assertEqual(receipt["knowledge_candidates"][0]["stable_key"], receipt["task_id"])

    def test_supported_candidate_types_are_classified_and_written(self) -> None:
        candidates = [
            self.candidate("decision", "api-policy", "Use the public adapter."),
            self.candidate("open_risk", "retry-risk", "Retries may duplicate writes."),
            self.candidate("root_cause", "timeout-root", "Timeout came from an expired lease."),
            self.candidate("milestone", "m0-accepted", "M0 acceptance passed."),
            self.candidate(
                "capability_observation",
                "rollback-observation",
                "User identified the rollback point before reveal.",
            ),
        ]

        result = self.compile(self.write_receipt("typed-task", candidates))
        cards = [self.read_card(path)[0] for path in self.card_files()]

        self.assertEqual(result["status"], "compiled")
        self.assertEqual({card["kind"] for card in cards}, {item["kind"] for item in candidates})
        capability = next(card for card in cards if card["kind"] == "capability_observation")
        self.assertEqual(capability["status"], "pending_review")

    def test_generated_active_card_passes_context_integrity(self) -> None:
        self.compile(
            self.write_receipt(
                "trusted-task",
                [self.candidate("decision", "retry-policy", "Use bounded retries.")],
            )
        )
        policy = load_memory_policy()
        policy["vault_root"] = str(self.vault)
        policy["private_policy"] = {
            "schema_version": 1,
            "ai_access": {"excluded_paths": [], "excluded_globs": []},
        }

        result = inspect_page(self.card_files()[0], policy=policy, today=date(2026, 8, 13))

        self.assertEqual(result["status"], "trusted")
        self.assertEqual(result["reasons"], [])

    def test_stable_key_is_idempotent_and_does_not_rewrite_same_card(self) -> None:
        receipt = self.write_receipt(
            "stable-task",
            [self.candidate("decision", "retry-policy", "Use bounded retries.")],
        )

        first = self.compile(receipt)
        path = self.card_files()[0]
        first_content = path.read_bytes()
        second = self.compile(receipt)

        self.assertEqual(first["cards"][0]["id"], second["cards"][0]["id"])
        self.assertEqual(second["cards"][0]["action"], "unchanged")
        self.assertEqual(path.read_bytes(), first_content)

    def test_new_decision_can_supersede_an_existing_card(self) -> None:
        self.compile(
            self.write_receipt(
                "old-task",
                [self.candidate("decision", "old-retry-policy", "Retry three times.")],
            )
        )
        old_path = self.card_files()[0]
        old_id = self.read_card(old_path)[0]["id"]

        result = self.compile(
            self.write_receipt(
                "new-task",
                [
                    self.candidate(
                        "decision",
                        "new-retry-policy",
                        "Retry once with idempotency.",
                        supersedes=["old-retry-policy"],
                    )
                ],
            )
        )
        old_frontmatter, _ = self.read_card(old_path)
        new_frontmatter, _ = self.read_card(next(path for path in self.card_files() if path != old_path))

        self.assertEqual(old_frontmatter["status"], "superseded")
        self.assertIn(old_id, new_frontmatter["supersedes"])
        self.assertEqual(result["cards"][0]["action"], "created")

    def test_conflicting_summary_keeps_active_card_and_creates_disputed_candidate(self) -> None:
        self.compile(
            self.write_receipt(
                "first-task",
                [self.candidate("decision", "retry-policy", "Retry three times.")],
            )
        )
        active_path = self.card_files()[0]

        result = self.compile(
            self.write_receipt(
                "conflict-task",
                [self.candidate("decision", "retry-policy", "Never retry writes.")],
            )
        )
        cards = [self.read_card(path)[0] for path in self.card_files()]

        self.assertEqual(self.read_card(active_path)[0]["status"], "active")
        self.assertIn("disputed", {card["status"] for card in cards})
        self.assertEqual(result["cards"][0]["action"], "disputed")

    def test_high_risk_and_shared_candidates_require_review(self) -> None:
        high_risk = self.compile(
            self.write_receipt(
                "security-task",
                [self.candidate("decision", "auth-policy", "Rotate sessions after login.")],
                risk="P1",
            )
        )
        shared = self.compile(
            self.write_receipt(
                "shared-task",
                [
                    self.candidate(
                        "root_cause",
                        "shared-timeout",
                        "Lease expiry caused the timeout.",
                        destination="shared",
                    )
                ],
            )
        )

        self.assertEqual(high_risk["cards"][0]["status"], "pending_review")
        self.assertEqual(shared["cards"][0]["status"], "pending_review")

    def test_sensitive_candidate_is_rejected_without_writing_content(self) -> None:
        secret = "api_key=top-secret-value"
        result = self.compile(
            self.write_receipt(
                "secret-task",
                [self.candidate("decision", "secret-policy", secret, sensitive=True)],
            )
        )

        self.assertEqual(result["cards"][0]["action"], "rejected")
        self.assertEqual(self.card_files(), [])
        self.assertNotIn(secret, json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
