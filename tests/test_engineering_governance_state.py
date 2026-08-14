from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "00_system" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from engineering_governance import (  # noqa: E402
    create_task_state,
    load_task_state,
    save_task_state,
    transition_task,
)


class EngineeringGovernanceStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_create_writes_complete_schema_to_the_only_local_state_path(self) -> None:
        state = create_task_state(self.repo, "Fix login failure", "code_change")

        path = self.repo / ".obsidiantowiki" / "task-state.json"
        self.assertTrue(path.exists())
        self.assertEqual(load_task_state(self.repo), state)
        self.assertEqual(state["schema_version"], 1)
        self.assertTrue(state["task_id"])
        self.assertEqual(state["status"], "investigating")
        self.assertEqual(state["risk"]["level"], "P2")
        self.assertEqual(state["scope"], {"allowed": [], "changed": [], "drift": []})
        self.assertEqual(state["diagnosis"], {"reproduction": None, "root_cause": None, "minimal_fix": None})
        self.assertEqual(list(self.repo.rglob("task-state.json")), [path])

    def test_valid_transition_is_persisted_with_reason_and_timestamp(self) -> None:
        create_task_state(self.repo, "Add export", "code_change")

        state = transition_task(self.repo, "planned", reason="acceptance and scope recorded")

        self.assertEqual(state["status"], "planned")
        self.assertEqual(state["timestamps"]["status_changed_at"], state["timestamps"]["updated_at"])
        self.assertEqual(state["history"][-1]["from"], "investigating")
        self.assertEqual(state["history"][-1]["to"], "planned")
        self.assertEqual(state["history"][-1]["reason"], "acceptance and scope recorded")

    def test_invalid_transition_is_rejected_without_changing_state(self) -> None:
        original = create_task_state(self.repo, "Add export", "code_change")

        with self.assertRaisesRegex(ValueError, "invalid task transition"):
            transition_task(self.repo, "closed")

        self.assertEqual(load_task_state(self.repo), original)

    def test_unknown_status_missing_task_id_and_invalid_risk_are_rejected(self) -> None:
        original = create_task_state(self.repo, "Add export", "code_change")
        invalid_cases = (
            {**original, "status": "guessing"},
            {**original, "task_id": ""},
            {**original, "risk": {**original["risk"], "level": "P9"}},
        )

        for invalid in invalid_cases:
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    save_task_state(self.repo, invalid)

        self.assertEqual(load_task_state(self.repo), original)

    def test_invalid_json_or_unknown_persisted_status_is_rejected(self) -> None:
        path = self.repo / ".obsidiantowiki" / "task-state.json"
        path.parent.mkdir()
        path.write_text("{broken", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "invalid task state JSON"):
            load_task_state(self.repo)

        path.write_text(json.dumps({"schema_version": 1, "task_id": "x", "status": "unknown"}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "unsupported task status"):
            load_task_state(self.repo)

    def test_failed_atomic_replace_preserves_previous_state_and_cleans_temp_file(self) -> None:
        original = create_task_state(self.repo, "Add export", "code_change")
        changed = {**original, "task": "Changed task"}

        with patch("engineering_governance.os.replace", side_effect=OSError("replace failed")):
            with self.assertRaisesRegex(OSError, "replace failed"):
                save_task_state(self.repo, changed)

        self.assertEqual(load_task_state(self.repo), original)
        state_dir = self.repo / ".obsidiantowiki"
        self.assertEqual([path for path in state_dir.iterdir() if path.suffix == ".tmp"], [])

    def test_task_state_is_covered_by_the_existing_gitignore_rule(self) -> None:
        rules = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertIn(".obsidiantowiki/", rules)


if __name__ == "__main__":
    unittest.main()
