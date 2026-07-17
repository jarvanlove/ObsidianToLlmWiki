from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "00_system" / "scripts" / "ui_governance.py"
OTW = REPO_ROOT / "00_system" / "scripts" / "otw.py"
PROJECT_SESSION = REPO_ROOT / "00_system" / "scripts" / "project_session.py"


def run(script: Path, args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args, "--format", "json"],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


class UiGovernanceTests(unittest.TestCase):
    def initialize(self, repo: Path, level: str, task_id: str = "settings-redesign") -> None:
        result = run(
            SCRIPT,
            [
                "init",
                "--repo-root",
                str(repo),
                "--task-id",
                task_id,
                "--task",
                "Redesign security settings",
                "--level",
                level,
            ],
            REPO_ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def add_evidence(self, repo: Path, task_id: str = "settings-redesign") -> None:
        screenshot = repo / "screenshots" / "settings-desktop.png"
        accessibility = repo / "reports" / "accessibility.md"
        screenshot.parent.mkdir(parents=True)
        accessibility.parent.mkdir(parents=True)
        screenshot.write_bytes(b"png")
        accessibility.write_text("passed\n", encoding="utf-8")
        qa = repo / "docs" / "design" / "qa" / f"{task_id}.md"
        qa.write_text("# Visual QA\n\nRelease: Pass\n", encoding="utf-8")
        result = run(
            SCRIPT,
            [
                "record-evidence",
                "--repo-root",
                str(repo),
                "--task-id",
                task_id,
                "--screenshot",
                "screenshots/settings-desktop.png",
                "--visual-qa",
                f"docs/design/qa/{task_id}.md",
                "--accessibility-report",
                "reports/accessibility.md",
            ],
            REPO_ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_u2_blocks_implementation_until_direction_is_approved_and_requires_evidence_to_close(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            self.initialize(repo, "U2")
            self.assertTrue((repo / "docs/design/UI_CONTRACT.md").exists())
            self.assertTrue((repo / "docs/design/UI_SKILL_REGISTRY.yaml").exists())
            self.assertTrue((repo / "docs/design/qa/settings-redesign.md").exists())

            blocked = run(
                SCRIPT,
                ["check", "--repo-root", str(repo), "--task-id", "settings-redesign", "--phase", "implementation"],
                REPO_ROOT,
            )
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn("visual direction is not approved", blocked.stdout)

            approved = run(
                SCRIPT,
                [
                    "set-stage",
                    "--repo-root",
                    str(repo),
                    "--task-id",
                    "settings-redesign",
                    "--stage",
                    "direction_approved",
                    "--approval-note",
                    "Direction B approved by product owner",
                ],
                REPO_ROOT,
            )
            self.assertEqual(approved.returncode, 0, approved.stderr)

            ready = run(
                SCRIPT,
                ["check", "--repo-root", str(repo), "--task-id", "settings-redesign", "--phase", "implementation"],
                REPO_ROOT,
            )
            self.assertEqual(ready.returncode, 0, ready.stderr)

            missing_evidence = run(
                SCRIPT,
                ["check", "--repo-root", str(repo), "--task-id", "settings-redesign", "--phase", "close"],
                REPO_ROOT,
            )
            self.assertNotEqual(missing_evidence.returncode, 0)
            self.assertIn("missing browser screenshot evidence", missing_evidence.stdout)

            self.add_evidence(repo)
            closed = run(
                SCRIPT,
                ["check", "--repo-root", str(repo), "--task-id", "settings-redesign", "--phase", "close"],
                REPO_ROOT,
            )
            self.assertEqual(closed.returncode, 0, closed.stderr)

    def test_u3_requires_an_approved_rfc_before_implementation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            self.initialize(repo, "U3", "brand-refresh")
            approved = run(
                SCRIPT,
                [
                    "set-stage",
                    "--repo-root",
                    str(repo),
                    "--task-id",
                    "brand-refresh",
                    "--stage",
                    "direction_approved",
                    "--approval-note",
                    "Approved visual direction",
                ],
                REPO_ROOT,
            )
            self.assertEqual(approved.returncode, 0, approved.stderr)

            blocked = run(
                SCRIPT,
                ["set-stage", "--repo-root", str(repo), "--task-id", "brand-refresh", "--stage", "implementation"],
                REPO_ROOT,
            )
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn("Design RFC is approved", blocked.stderr)

            rfc = run(
                SCRIPT,
                [
                    "approve-rfc",
                    "--repo-root",
                    str(repo),
                    "--task-id",
                    "brand-refresh",
                    "--approval-note",
                    "Approved migration plan",
                ],
                REPO_ROOT,
            )
            self.assertEqual(rfc.returncode, 0, rfc.stderr)
            implementation = run(
                SCRIPT,
                ["set-stage", "--repo-root", str(repo), "--task-id", "brand-refresh", "--stage", "implementation"],
                REPO_ROOT,
            )
            self.assertEqual(implementation.returncode, 0, implementation.stderr)

    def test_u0_does_not_create_ui_control_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            result = run(
                SCRIPT,
                [
                    "init",
                    "--repo-root",
                    str(repo),
                    "--task-id",
                    "api-fix",
                    "--task",
                    "Fix API timeout",
                    "--level",
                    "U0",
                ],
                REPO_ROOT,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((repo / "docs/design/UI_CONTRACT.md").exists())
            self.assertEqual(json.loads(result.stdout)["status"], "not_created")

    def test_unified_runtime_forwards_ui_governance_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            result = run(
                OTW,
                [
                    "ui",
                    "assess",
                    "--repo-root",
                    str(repo),
                    "--task",
                    "Fix a form error state",
                    "--level",
                    "U1",
                ],
                REPO_ROOT,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["ui_level"], "U1")

    def test_project_close_rejects_ui_task_without_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            source = repo / "screen.tsx"
            source.write_text("export const screen = 1;\n", encoding="utf-8")
            subprocess.run(["git", "add", "screen.tsx"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True)
            source.write_text("export const screen = 2;\n", encoding="utf-8")
            self.initialize(repo, "U2")
            approval = run(
                SCRIPT,
                [
                    "set-stage",
                    "--repo-root",
                    str(repo),
                    "--task-id",
                    "settings-redesign",
                    "--stage",
                    "direction_approved",
                    "--approval-note",
                    "Approved direction",
                ],
                REPO_ROOT,
            )
            self.assertEqual(approval.returncode, 0, approval.stderr)

            blocked = run(
                PROJECT_SESSION,
                [
                    "close",
                    "--repo-root",
                    str(repo),
                    "--ui-task",
                    "settings-redesign",
                    "--verification",
                    "unit tests passed",
                ],
                REPO_ROOT,
            )
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn("UI task cannot close", blocked.stderr)
            self.assertFalse((repo / ".obsidiantowiki/session-receipt.json").exists())

            self.add_evidence(repo)
            closed = run(
                PROJECT_SESSION,
                [
                    "close",
                    "--repo-root",
                    str(repo),
                    "--ui-task",
                    "settings-redesign",
                    "--verification",
                    "unit tests passed",
                ],
                REPO_ROOT,
            )
            self.assertEqual(closed.returncode, 0, closed.stderr)
            self.assertTrue(json.loads(closed.stdout)["ui_governance"]["passed"])


if __name__ == "__main__":
    unittest.main()
