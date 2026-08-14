from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "00_system" / "scripts" / "project_session.py"


def evidence_json() -> str:
    return json.dumps(
        {
            "kind": "test",
            "command": "python -m unittest tests.test_project_session_receipt -v",
            "exit_code": 0,
            "result": "passed",
            "recorded_at": "2026-08-14T11:00:00+08:00",
            "source": "deterministic",
        }
    )


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True, encoding="utf-8")


class ProjectSessionReceiptTests(unittest.TestCase):
    def test_start_uses_governed_state_and_does_not_overwrite_an_open_task(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            run(["git", "init"], repo)
            run(["git", "config", "user.email", "test@example.com"], repo)
            run(["git", "config", "user.name", "Test"], repo)
            (repo / ".gitignore").write_text(".obsidiantowiki/\n", encoding="utf-8")
            (repo / "feature.py").write_text("value = 1\n", encoding="utf-8")
            run(["git", "add", "."], repo)
            run(["git", "commit", "-m", "initial"], repo)

            started = run(
                [sys.executable, str(SCRIPT), "start", "--repo-root", str(repo), "--task", "First task", "--format", "json"],
                REPO_ROOT,
            )
            self.assertEqual(started.returncode, 0, started.stderr)
            first = json.loads(started.stdout)
            state_path = repo / ".obsidiantowiki" / "task-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["status"], "investigating")
            self.assertEqual(state["baseline"]["head"], run(["git", "rev-parse", "HEAD"], repo).stdout.strip())

            second = run(
                [sys.executable, str(SCRIPT), "start", "--repo-root", str(repo), "--task", "Second task", "--format", "json"],
                REPO_ROOT,
            )
            self.assertEqual(second.returncode, 0, second.stderr)
            resumed = json.loads(second.stdout)
            persisted = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(resumed["task_id"], first["task_id"])
            self.assertEqual(resumed["task"], "First task")
            self.assertEqual(resumed["requested_task"], "Second task")
            self.assertEqual(persisted["task_id"], first["task_id"])

            checked = run([sys.executable, str(SCRIPT), "check", "--repo-root", str(repo), "--format", "json"], REPO_ROOT)
            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertEqual(json.loads(checked.stdout)["engineering_task"]["task_id"], first["task_id"])

    def test_start_migrates_the_previous_active_state_without_changing_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            run(["git", "init"], repo)
            run(["git", "config", "user.email", "test@example.com"], repo)
            run(["git", "config", "user.name", "Test"], repo)
            (repo / ".gitignore").write_text(".obsidiantowiki/\n", encoding="utf-8")
            (repo / "feature.py").write_text("value = 1\n", encoding="utf-8")
            run(["git", "add", "."], repo)
            run(["git", "commit", "-m", "initial"], repo)
            state_path = repo / ".obsidiantowiki" / "task-state.json"
            state_path.parent.mkdir()
            state_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "status": "active",
                        "task_id": "legacy-task-id",
                        "task": "Legacy active task",
                        "knowledge_candidates": [{"kind": "milestone", "stable_key": "legacy"}],
                    }
                ),
                encoding="utf-8",
            )

            started = run(
                [sys.executable, str(SCRIPT), "start", "--repo-root", str(repo), "--task", "Legacy active task", "--format", "json"],
                REPO_ROOT,
            )

            self.assertEqual(started.returncode, 0, started.stderr)
            payload = json.loads(started.stdout)
            migrated = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["task_id"], "legacy-task-id")
            self.assertEqual(migrated["status"], "investigating")
            self.assertEqual(migrated["baseline"]["head"], run(["git", "rev-parse", "HEAD"], repo).stdout.strip())
            self.assertEqual(migrated["knowledge_candidates"][0]["stable_key"], "legacy")

    def test_close_requires_explicit_resolution_of_every_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            run(["git", "init"], repo)
            run(["git", "config", "user.email", "test@example.com"], repo)
            run(["git", "config", "user.name", "Test"], repo)
            source = repo / "feature.py"
            source.write_text("value = 1\n", encoding="utf-8")
            run(["git", "add", "feature.py"], repo)
            run(["git", "commit", "-m", "initial"], repo)
            source.write_text("value = 2\n", encoding="utf-8")

            closed = run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "close",
                    "--repo-root",
                    str(repo),
                    "--evidence",
                    evidence_json(),
                    "--format",
                    "json",
                ],
                REPO_ROOT,
            )
            self.assertEqual(closed.returncode, 0, closed.stderr)
            close_payload = json.loads(closed.stdout)
            receipt_path = Path(close_payload["receipt_path"])
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["status"], "pending")
            self.assertTrue(all(item["status"] == "pending" for item in receipt["candidates"]))

            checked = run(
                [sys.executable, str(SCRIPT), "check", "--repo-root", str(repo), "--format", "json"],
                REPO_ROOT,
            )
            self.assertEqual(json.loads(checked.stdout)["cockpit_state"], "not_attached")
            self.assertEqual(json.loads(checked.stdout)["session_receipt"]["status"], "pending")

            resolve_command = [sys.executable, str(SCRIPT), "resolve", "--repo-root", str(repo), "--format", "json"]
            for candidate in receipt["candidates"]:
                resolve_command.extend(["--resolution", f"{candidate['id']}=not_applicable"])
            resolved = run(resolve_command, REPO_ROOT)
            self.assertEqual(resolved.returncode, 0, resolved.stderr)
            self.assertEqual(json.loads(resolved.stdout)["status"], "resolved")

    def test_resolved_receipt_with_uncommitted_changes_is_closed_pending_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            run(["git", "init"], repo)
            run(["git", "config", "user.email", "test@example.com"], repo)
            run(["git", "config", "user.name", "Test"], repo)
            source = repo / "feature.py"
            source.write_text("value = 1\n", encoding="utf-8")
            run(["git", "add", "feature.py"], repo)
            run(["git", "commit", "-m", "initial"], repo)
            wiki_root = repo / "wiki"
            (repo / "wiki.context.json").write_text(
                json.dumps({"wiki_root": str(wiki_root), "project_slug": "demo"}),
                encoding="utf-8",
            )
            source.write_text("value = 2\n", encoding="utf-8")

            closed = run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "close",
                    "--repo-root",
                    str(repo),
                    "--evidence",
                    evidence_json(),
                    "--format",
                    "json",
                ],
                REPO_ROOT,
            )
            self.assertEqual(closed.returncode, 0, closed.stderr)
            receipt = json.loads(Path(json.loads(closed.stdout)["receipt_path"]).read_text(encoding="utf-8"))
            resolve_command = [sys.executable, str(SCRIPT), "resolve", "--repo-root", str(repo), "--format", "json"]
            for candidate in receipt["candidates"]:
                resolve_command.extend(["--resolution", f"{candidate['id']}=not_applicable"])
            resolved = run(resolve_command, REPO_ROOT)
            self.assertEqual(resolved.returncode, 0, resolved.stderr)

            checked = run(
                [sys.executable, str(SCRIPT), "check", "--repo-root", str(repo), "--format", "json"],
                REPO_ROOT,
            )
            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertEqual(json.loads(checked.stdout)["cockpit_state"], "closed_pending_commit")


if __name__ == "__main__":
    unittest.main()
