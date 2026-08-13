from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "00_system" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from memory_compiler import compile_projections, estimate_tokens  # noqa: E402
from wiki_lib import parse_frontmatter, render_markdown  # noqa: E402


class MemoryProjectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.vault = Path(self.tempdir.name)
        self.project = self.vault / "20_projects" / "active" / "demo"
        self.memory = self.project / "memory"
        self.memory.mkdir(parents=True)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def card(self, card_id: str, kind: str, summary: str, *, status: str = "active", age: int = 0) -> None:
        effective = date(2026, 8, 13) - timedelta(days=age)
        frontmatter = {
            "title": summary,
            "type": "项目记忆卡",
            "project": "demo",
            "id": card_id,
            "stable_key": card_id.lower(),
            "kind": kind,
            "status": status,
            "effective_from": effective.isoformat(),
            "summary": summary,
            "evidence_refs": [f"test:{card_id}"],
        }
        (self.memory / f"{card_id}.md").write_text(
            render_markdown(frontmatter, f"# {summary}\n\n{summary}"), encoding="utf-8"
        )

    def test_seven_current_projections_are_bounded_and_filter_inactive_cards(self) -> None:
        self.card("DEC-1", "decision", "Use the public runtime.")
        self.card("DEC-OLD", "decision", "Use copied private scripts.", status="superseded")
        self.card("RISK-1", "open_risk", "Migration needs explicit approval.")
        self.card("ROOT-1", "root_cause", "Context failed because the source page was stale.")
        self.card("CAP-1", "capability_observation", "Unreviewed skill claim.", status="pending_review")

        result = compile_projections(
            wiki_root=self.vault, project_slug="demo", dry_run=True, today=date(2026, 8, 13)
        )

        self.assertEqual(len(result["pages"]), 7)
        combined = "\n".join(page["content"] for page in result["pages"])
        self.assertIn("Use the public runtime.", combined)
        self.assertNotIn("Use copied private scripts.", combined)
        self.assertNotIn("Unreviewed skill claim.", combined)
        for page in result["pages"]:
            self.assertLessEqual(estimate_tokens(page["content"]), page["token_budget"])
            frontmatter, _body = parse_frontmatter(page["content"])
            self.assertTrue(str(frontmatter["type"]).startswith("项目"))
            self.assertEqual(frontmatter["status"], "活跃")
        self.assertFalse(any(self.project.glob("*.md")))

    def test_timeline_keeps_only_latest_thirty_events_from_ninety_days(self) -> None:
        for index in range(40):
            self.card(f"MILE-{index:02d}", "milestone", f"Milestone {index}", age=index * 2)
        self.card("MILE-OLD", "milestone", "Very old event", age=100)

        result = compile_projections(
            wiki_root=self.vault, project_slug="demo", dry_run=True, today=date(2026, 8, 13)
        )
        timeline = next(page for page in result["pages"] if page["name"] == "时间线.md")["content"]

        self.assertEqual(timeline.count("- 2026-"), 30)
        self.assertNotIn("Very old event", timeline)

    def test_apply_refuses_to_overwrite_an_unmigrated_core_page(self) -> None:
        overview = self.project / "概览.md"
        overview.write_text("# User overview\n\nKeep this customization.\n", encoding="utf-8")
        self.card("DEC-1", "decision", "Use the public runtime.")

        result = compile_projections(
            wiki_root=self.vault, project_slug="demo", dry_run=False, today=date(2026, 8, 13)
        )

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(overview.read_text(encoding="utf-8"), "# User overview\n\nKeep this customization.\n")


if __name__ == "__main__":
    unittest.main()
