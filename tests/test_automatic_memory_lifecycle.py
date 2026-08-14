from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "00_system" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from memory_compiler import PROJECTION_START, compile_projections, estimate_tokens  # noqa: E402
from project_session import (  # noqa: E402
    build_receipt,
    finalize_memory_maintenance,
    memory_health,
    resolve_receipt,
    start_report,
)
from wiki_lib import render_markdown  # noqa: E402


def deterministic_evidence() -> list[dict[str, object]]:
    return [{
        "kind": "test",
        "command": "python -m unittest tests.test_automatic_memory_lifecycle -v",
        "exit_code": 0,
        "result": "passed",
        "recorded_at": "2026-08-14T11:00:00+08:00",
        "source": "deterministic",
    }]


class AutomaticMemoryLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.repo = self.root / "repo"
        self.vault = self.root / "vault"
        self.repo.mkdir()
        self.vault.mkdir()
        subprocess.run(["git", "init"], cwd=self.repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.repo, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=self.repo, check=True)
        for name in (
            "PRODUCT_SPEC.md",
            "ARCHITECTURE.md",
            "TASKS.md",
            "TESTING.md",
            "SECURITY.md",
            "DEPLOYMENT.md",
            "OPERATIONS.md",
            "CHANGELOG.md",
        ):
            (self.repo / name).write_text(f"# {name}\n", encoding="utf-8")
        (self.repo / "docs" / "adr").mkdir(parents=True)
        (self.repo / "docs" / "ai-workflows").mkdir(parents=True)
        self.project = self.vault / "20_projects" / "active" / "demo"
        self.project.mkdir(parents=True)
        context = {
            "wiki_root": str(self.vault),
            "project_slug": "demo",
            "project_memory": "20_projects/active/demo/project.memory.md",
        }
        for key, name in (
            ("project_index", "索引.md"),
            ("project_overview", "概览.md"),
            ("project_architecture", "架构.md"),
            ("project_decisions", "决策.md"),
            ("project_tasks", "任务.md"),
            ("project_risks", "风险.md"),
            ("project_timeline", "时间线.md"),
        ):
            context[key] = f"20_projects/active/demo/{name}"
        (self.repo / "wiki.context.json").write_text(json.dumps(context), encoding="utf-8")
        (self.project / "索引.md").write_text("# demo\n", encoding="utf-8")
        compile_projections(wiki_root=self.vault, project_slug="demo")
        subprocess.run(["git", "add", "."], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=self.repo, check=True, capture_output=True)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_start_checks_context_budget_and_creates_initial_snapshot_candidate(self) -> None:
        report = start_report(self.repo, "Implement passive memory")

        lifecycle = report["memory_lifecycle"]
        self.assertIn(lifecycle["context_status"], {"ready", "degraded", "missing"})
        self.assertLessEqual(lifecycle["token_usage"]["used"], lifecycle["token_usage"]["limit"])
        self.assertEqual(lifecycle["candidate_count"], 1)
        state = json.loads((self.repo / ".obsidiantowiki" / "task-state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["task_id"], report["task_id"])

    def test_close_candidate_waits_for_receipt_resolution_then_compiles_memory(self) -> None:
        started = start_report(self.repo, "Implement passive memory")
        report = {
            "task": started["task"],
            "task_id": started["task_id"],
            "verification": "python -m unittest: passed",
            "evidence": deterministic_evidence(),
            "changed_files": ["feature.py"],
            "control_file_update_candidates": [],
            "wiki_file_back_candidates": [],
        }
        receipt = build_receipt(self.repo, report)
        receipt_path = self.repo / ".obsidiantowiki" / "session-receipt.json"
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

        self.assertEqual(list((self.project / "memory").glob("*.md")), [])
        resolved = resolve_receipt(receipt_path, [])
        maintained = finalize_memory_maintenance(self.repo, receipt_path, resolved)

        self.assertEqual(maintained["memory_status"], "current")
        self.assertTrue(list((self.project / "memory").glob("*.md")))
        self.assertFalse((self.repo / ".obsidiantowiki" / "cockpit").exists())

    def test_memory_failure_preserves_resolved_task_and_marks_repair(self) -> None:
        started = start_report(self.repo, "Implement passive memory")
        receipt = build_receipt(
            self.repo,
            {
                "task": started["task"],
                "task_id": started["task_id"],
                "verification": "passed",
                "changed_files": [],
                "control_file_update_candidates": [],
                "wiki_file_back_candidates": [],
            },
        )
        receipt_path = self.repo / "receipt.json"
        receipt["status"] = "resolved"
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
        (self.project / "概览.md").write_text("# user owned\n", encoding="utf-8")

        result = finalize_memory_maintenance(self.repo, receipt_path, receipt)

        self.assertEqual(result["status"], "resolved")
        self.assertEqual(result["memory_status"], "pending_memory_repair")
        self.assertEqual(result["memory_maintenance"]["reason"], "unmanaged_core_pages_require_migration")

    def test_high_risk_memory_failure_does_not_claim_governance_close(self) -> None:
        started = start_report(self.repo, "Change authentication boundary")
        receipt = build_receipt(
            self.repo,
            {
                "task": started["task"],
                "task_id": started["task_id"],
                "risk": {"level": "P1"},
                "verification": "passed",
                "changed_files": ["auth.py"],
                "control_file_update_candidates": [],
                "wiki_file_back_candidates": [],
            },
        )
        receipt_path = self.repo / "high-risk-receipt.json"
        receipt["status"] = "resolved"
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
        (self.project / "概览.md").write_text("# user owned\n", encoding="utf-8")

        result = finalize_memory_maintenance(self.repo, receipt_path, receipt)

        self.assertEqual(result["status"], "resolved")
        self.assertEqual(result["governance_status"], "blocked_memory_repair")

    def test_over_budget_projection_is_detected_and_rebuilt_after_resolution(self) -> None:
        tasks = self.project / "任务.md"
        tasks.write_text(tasks.read_text(encoding="utf-8") + ("x" * 10000), encoding="utf-8")
        health = memory_health(self.repo)
        self.assertIn("projection_over_budget", health["maintenance_reasons"])

        compile_projections(wiki_root=self.vault, project_slug="demo")

        self.assertLessEqual(estimate_tokens(tasks.read_text(encoding="utf-8")), 1500)

    def test_ninety_day_inactivity_returns_a_bounded_recovery_summary(self) -> None:
        memory = self.project / "memory"
        memory.mkdir()
        old = (date.today() - timedelta(days=91)).isoformat()
        (memory / "MILE-OLD.md").write_text(
            render_markdown(
                {
                    "title": "Old milestone",
                    "type": "项目记忆卡",
                    "project": "demo",
                    "id": "MILE-OLD",
                    "stable_key": "old",
                    "kind": "milestone",
                    "status": "active",
                    "effective_from": old,
                    "summary": "Old milestone",
                    "evidence_refs": ["git:old"],
                },
                "# Old milestone\n",
            ),
            encoding="utf-8",
        )

        health = memory_health(self.repo)

        self.assertEqual(health["activity_state"], "cooled")
        self.assertIn("90", health["recovery_summary"])
        self.assertLess(len(health["recovery_summary"]), 300)


if __name__ == "__main__":
    unittest.main()
