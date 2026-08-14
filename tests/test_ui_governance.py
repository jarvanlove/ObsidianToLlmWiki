from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


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


def verification_evidence_json() -> str:
    return json.dumps({
        "kind": "test",
        "command": "python -m unittest tests.test_ui_governance -v",
        "exit_code": 0,
        "result": "passed",
        "recorded_at": "2026-08-14T11:00:00+08:00",
        "source": "deterministic",
    })


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

    def test_visual_direction_registry_has_six_defaults_and_nineteen_sources(self) -> None:
        result = run(SCRIPT, ["list-directions"], REPO_ROOT)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        directions = payload["directions"]
        self.assertEqual(len(directions), 19)
        self.assertEqual(sum(item["tier"] == "default" for item in directions), 6)
        self.assertEqual(payload["fallback_direction_id"], "mist-teal-ink")
        corrected = next(item for item in directions if item["source_number"] == 17)
        self.assertEqual(corrected["primary"], {"name": "青矾绿", "hex": "#2C9678"})
        self.assertEqual(corrected["accent"], {"name": "灰食白", "hex": "#F5F4F7"})

    def test_feedback_recommends_three_plain_language_default_directions(self) -> None:
        result = run(
            SCRIPT,
            [
                "recommend-directions",
                "--feedback",
                "这个感觉太冷，也不够高级",
                "--product-context",
                "会员权益页",
            ],
            REPO_ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(len(payload["recommendations"]), 3)
        self.assertEqual(payload["recommendations"][0]["id"], "burgundy-paper")
        self.assertEqual(payload["recommendations"][0]["label"], "高级氛围")
        self.assertNotIn("primary", payload["recommendations"][0])

        forwarded = run(
            OTW,
            [
                "ui",
                "recommend-directions",
                "--repo-root",
                str(REPO_ROOT),
                "--feedback",
                "太花了，想更清楚正式",
            ],
            REPO_ROOT,
        )
        self.assertEqual(forwarded.returncode, 0, forwarded.stderr)
        self.assertEqual(json.loads(forwarded.stdout)["recommendations"][0]["id"], "paper-iris")

    def test_user_can_confirm_a_recommended_direction_before_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            self.initialize(repo, "U2", "membership-page")
            selected = run(
                SCRIPT,
                [
                    "select-direction",
                    "--repo-root",
                    str(repo),
                    "--task-id",
                    "membership-page",
                    "--visual-direction",
                    "burgundy-paper",
                    "--approval-note",
                    "User replied: use the first one",
                ],
                REPO_ROOT,
            )
            self.assertEqual(selected.returncode, 0, selected.stderr)
            task = yaml.safe_load((repo / "docs/design/ui-tasks/membership-page.yaml").read_text(encoding="utf-8"))
            self.assertEqual(task["visual_direction"]["id"], "burgundy-paper")
            self.assertEqual(task["visual_direction"]["selection"], "user_confirmed")

            approved = run(
                SCRIPT,
                [
                    "set-stage",
                    "--repo-root",
                    str(repo),
                    "--task-id",
                    "membership-page",
                    "--stage",
                    "direction_approved",
                    "--approval-note",
                    "User approved the warm premium direction",
                ],
                REPO_ROOT,
            )
            self.assertEqual(approved.returncode, 0, approved.stderr)
            baseline = json.loads((repo / "docs/design/UI_VISUAL_BASELINE.json").read_text(encoding="utf-8"))
            self.assertEqual(baseline["direction"]["id"], "burgundy-paper")

    def test_existing_baseline_cannot_shift_from_feedback_on_u2(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            self.initialize(repo, "U1", "first-screen")
            self.initialize(repo, "U2", "new-flow")
            blocked = run(
                SCRIPT,
                [
                    "select-direction",
                    "--repo-root",
                    str(repo),
                    "--task-id",
                    "new-flow",
                    "--visual-direction",
                    "burgundy-paper",
                    "--approval-note",
                    "User wants a warmer overall feel",
                ],
                REPO_ROOT,
            )
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn("existing project style is fixed", blocked.stderr)

    def test_u1_uses_a_stable_fallback_baseline_and_controlled_direction_needs_user_note(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            self.initialize(repo, "U1", "first-screen")
            baseline = json.loads((repo / "docs/design/UI_VISUAL_BASELINE.json").read_text(encoding="utf-8"))
            self.assertEqual(baseline["direction"]["id"], "mist-teal-ink")

            locked = run(
                SCRIPT,
                [
                    "init",
                    "--repo-root",
                    str(repo),
                    "--task-id",
                    "second-screen",
                    "--task",
                    "Add a dashboard screen",
                    "--level",
                    "U1",
                    "--visual-direction",
                    "ember-charcoal",
                ],
                REPO_ROOT,
            )
            self.assertNotEqual(locked.returncode, 0)
            self.assertIn("baseline is locked", locked.stderr)

        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            missing_note = run(
                SCRIPT,
                [
                    "init",
                    "--repo-root",
                    str(repo),
                    "--task-id",
                    "campaign-screen",
                    "--task",
                    "Create a campaign screen",
                    "--level",
                    "U1",
                    "--visual-direction",
                    "klein-gold",
                ],
                REPO_ROOT,
            )
            self.assertNotEqual(missing_note.returncode, 0)
            self.assertIn("explicit user selection note", missing_note.stderr)

            selected = run(
                SCRIPT,
                [
                    "init",
                    "--repo-root",
                    str(repo),
                    "--task-id",
                    "campaign-screen",
                    "--task",
                    "Create a campaign screen",
                    "--level",
                    "U1",
                    "--visual-direction",
                    "klein-gold",
                    "--approval-note",
                    "User selected the energetic campaign direction",
                ],
                REPO_ROOT,
            )
            self.assertEqual(selected.returncode, 0, selected.stderr)

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
                    "--evidence",
                    verification_evidence_json(),
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
                    "--evidence",
                    verification_evidence_json(),
                ],
                REPO_ROOT,
            )
            self.assertEqual(closed.returncode, 0, closed.stderr)
            close_payload = json.loads(closed.stdout)
            self.assertTrue(close_payload["ui_governance"]["passed"])
            receipt = json.loads(Path(close_payload["receipt_path"]).read_text(encoding="utf-8"))
            self.assertEqual(receipt["gate_results"]["verification_evidence"]["status"], "passed")


if __name__ == "__main__":
    unittest.main()
