from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from tests.test_support import load_script_module


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "00_system" / "scripts"
context_contract = load_script_module(SCRIPT_DIR / "context_contract.py", "context_contract_test_module")


def memory_page(*, page_id: str, page_type: str, body: str, source: bool = True) -> str:
    source_lines = "source_refs:\n  - task:task-1\n" if source else ""
    return (
        "---\n"
        f"id: {page_id}\n"
        f"title: {page_id}\n"
        f"type: {page_type}\n"
        "domain: 项目\n"
        "project: demo\n"
        "status: active\n"
        "updated: 2026-08-13\n"
        f"summary: {page_id} summary.\n"
        f"{source_lines}"
        "---\n\n"
        f"# {page_id}\n\n{body}\n"
    )


class ContextContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.repo = self.root / "repo"
        self.vault = self.root / "vault"
        self.repo.mkdir()
        self.memory = self.vault / "20_projects" / "active" / "demo" / "project.memory.md"
        self.cards = self.vault / "20_projects" / "active" / "demo" / "memory-cards"
        self.cards.mkdir(parents=True)

        for name in ("PRODUCT_SPEC.md", "ARCHITECTURE.md", "TASKS.md"):
            (self.repo / name).write_text(f"# {name}\n\nCurrent {name} contract for bounded context.\n", encoding="utf-8")
        self.memory.write_text(
            memory_page(page_id="project-memory", page_type="项目运行记忆", body="Current objective and next step."),
            encoding="utf-8",
        )
        (self.repo / "wiki.context.json").write_text(
            json.dumps(
                {
                    "wiki_root": str(self.vault),
                    "project_slug": "demo",
                    "project_memory": "20_projects/active/demo/project.memory.md",
                }
            ),
            encoding="utf-8",
        )
        self.now = datetime(2026, 8, 13, 8, 0, tzinfo=timezone.utc)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def candidate(self, index: int, *, kind: str, score: int, body: str | None = None) -> dict[str, object]:
        path = self.cards / f"card-{index}.md"
        path.write_text(
            memory_page(
                page_id=f"card-{index}",
                page_type="项目决策" if kind == "active_decision" else "项目风险",
                body=body or f"Evidence for card {index}.",
            ),
            encoding="utf-8",
        )
        return {
            "path": path.relative_to(self.vault).as_posix(),
            "title": f"card-{index}",
            "kind": kind,
            "score": score,
            "snippet": body or f"Evidence for card {index}.",
        }

    def build(
        self,
        candidates: list[dict[str, object]],
        *,
        contract: dict[str, object] | None = None,
        now: datetime | None = None,
    ) -> dict[str, object]:
        return context_contract.build_context(
            repo_root=self.repo,
            wiki_root=self.vault,
            query="bounded context evidence",
            task_id="task-123",
            candidates=candidates,
            contract=contract,
            now=now or self.now,
            write_receipt=True,
        )

    def test_defaults_include_minimum_controls_memory_and_at_most_six_cards(self) -> None:
        candidates = [
            self.candidate(index, kind="active_decision" if index % 2 else "open_risk", score=100 - index)
            for index in range(1, 9)
        ]
        result = self.build(candidates)

        self.assertEqual(result["contract"]["token_budget"], 6000)
        self.assertEqual(result["contract"]["max_cards"], 6)
        self.assertEqual([item["path"] for item in result["controls"]], ["PRODUCT_SPEC.md", "ARCHITECTURE.md", "TASKS.md"])
        self.assertTrue(result["project_memory"]["path"].endswith("project.memory.md"))
        self.assertEqual(len(result["cards"]), 6)
        self.assertLessEqual(result["token_usage"]["used"], 6000)
        self.assertTrue(Path(result["receipt_path"]).exists())

    def test_quarantined_card_is_excluded_from_context(self) -> None:
        broken = self.cards / "broken.md"
        broken.write_text("---\ntitle: Broken\n", encoding="utf-8")
        candidates = [
            {
                "path": broken.relative_to(self.vault).as_posix(),
                "title": "broken",
                "kind": "active_decision",
                "score": 999,
                "snippet": "must never reach the model",
            },
            self.candidate(1, kind="open_risk", score=10),
        ]
        result = self.build(candidates)

        self.assertEqual([item["id"] for item in result["cards"]], ["card-1"])
        self.assertEqual(result["excluded"][0]["trust_state"], "quarantined")
        self.assertNotIn("must never reach the model", result["context"])

    def test_missing_required_kind_is_explicit(self) -> None:
        result = self.build([])
        self.assertEqual(result["status"], "missing")
        self.assertEqual(result["missing"], ["active_decision", "open_risk"])
        self.assertNotIn("no restrictions", result["context"].lower())

    def test_same_task_and_content_have_stable_hash_across_receipt_times(self) -> None:
        candidates = [
            self.candidate(1, kind="active_decision", score=20),
            self.candidate(2, kind="open_risk", score=10),
        ]
        first = self.build(candidates, now=self.now)
        second = self.build(candidates, now=datetime(2026, 8, 13, 9, 0, tzinfo=timezone.utc))
        self.assertEqual(first["content_hash"], second["content_hash"])
        self.assertNotEqual(first["receipt"]["generated_at"], second["receipt"]["generated_at"])

    def test_budget_drops_whole_low_priority_cards_without_string_truncation(self) -> None:
        high = self.candidate(1, kind="active_decision", score=100, body="HIGH " * 20)
        medium = self.candidate(2, kind="open_risk", score=80, body="MEDIUM " * 20)
        low = self.candidate(3, kind="active_decision", score=1, body="LOW " * 200)
        contract = context_contract.default_contract("task-123")
        contract["token_budget"] = 420
        result = self.build([low, medium, high], contract=contract)

        ids = [item["id"] for item in result["cards"]]
        self.assertIn("card-1", ids)
        self.assertNotIn("card-3", ids)
        self.assertNotIn("...", result["context"])
        self.assertLessEqual(result["token_usage"]["used"], 420)

    def test_receipt_records_l0_l1_cards_budget_missing_and_conflicts(self) -> None:
        candidate = self.candidate(1, kind="active_decision", score=20)
        result = self.build([candidate])
        receipt = json.loads(Path(result["receipt_path"]).read_text(encoding="utf-8"))

        self.assertEqual(receipt["query"], "bounded context evidence")
        self.assertEqual(receipt["task_id"], "task-123")
        self.assertIn("git_head", receipt["l0"])
        self.assertEqual(len(receipt["l1_files"]), 3)
        self.assertEqual(receipt["cards"][0]["id"], "card-1")
        self.assertEqual(receipt["budget"]["limit"], 6000)
        self.assertEqual(receipt["missing"], ["open_risk"])
        self.assertEqual(receipt["conflicts"], [])
        self.assertEqual(receipt["content_hash"], result["content_hash"])


if __name__ == "__main__":
    unittest.main()
