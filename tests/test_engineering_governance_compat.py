from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "00_system" / "scripts"
PROJECT_SESSION = SCRIPTS_DIR / "project_session.py"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from engineering_governance import load_task_state  # noqa: E402
from project_session import load_receipt  # noqa: E402


class EngineeringGovernanceCompatibilityTests(unittest.TestCase):
    def test_release_candidate_declares_all_governance_contract_versions(self) -> None:
        release = json.loads(
            (REPO_ROOT / "00_system/registry/runtime_release.json").read_text(encoding="utf-8")
        )

        self.assertEqual(release["runtime_version"], "2.0.0-rc.1")
        self.assertEqual(release["release_channel"], "release-candidate")
        self.assertEqual(release["project_scaffold_version"], 4)
        self.assertEqual(release["receipt_schema_version"], 2)
        self.assertEqual(release["task_state_schema_version"], 1)

    def test_v1_receipt_remains_readable_as_blocked_v2_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "session-receipt.json"
            path.write_text(
                json.dumps({"schema_version": 1, "status": "resolved", "verification": "legacy pass"}),
                encoding="utf-8",
            )

            receipt = load_receipt(path)

        self.assertEqual(receipt["schema_version"], 2)
        self.assertEqual(receipt["legacy_schema_version"], 1)
        self.assertEqual(receipt["status"], "blocked")

    def test_new_runtime_can_check_and_close_a_legacy_active_task(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            state_path = repo / ".obsidiantowiki" / "task-state.json"
            state_path.parent.mkdir()
            state_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "task_id": "legacy-task",
                        "task": "Legacy active task",
                        "status": "active",
                        "started_at": "2026-08-01T10:00:00+08:00",
                    }
                ),
                encoding="utf-8",
            )

            checked = subprocess.run(
                [sys.executable, str(PROJECT_SESSION), "check", "--repo-root", str(repo), "--format", "json"],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertEqual(json.loads(checked.stdout)["engineering_task"]["task_id"], "legacy-task")
            self.assertEqual(load_task_state(repo)["migrated_from"], "legacy_active")

            evidence = json.dumps(
                {
                    "kind": "compatibility",
                    "command": "legacy project close rehearsal",
                    "exit_code": 0,
                    "result": "passed",
                    "recorded_at": "2026-08-14T12:00:00+08:00",
                    "source": "deterministic",
                }
            )
            closed = subprocess.run(
                [
                    sys.executable,
                    str(PROJECT_SESSION),
                    "close",
                    "--repo-root",
                    str(repo),
                    "--evidence",
                    evidence,
                    "--format",
                    "json",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(closed.returncode, 0, closed.stderr)
            self.assertEqual(json.loads(closed.stdout)["receipt_status"], "pending")

    def test_newer_task_state_schema_is_rejected_instead_of_guessed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            state_path = repo / ".obsidiantowiki" / "task-state.json"
            state_path.parent.mkdir()
            state_path.write_text(json.dumps({"schema_version": 2}), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "unsupported task state schema"):
                load_task_state(repo)


if __name__ == "__main__":
    unittest.main()
