from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "00_system" / "scripts" / "project_session.py"


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True, encoding="utf-8")


class ProjectSessionReceiptTests(unittest.TestCase):
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
                    "--verification",
                    "unit tests passed",
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
                    "--verification",
                    "unit tests passed",
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
