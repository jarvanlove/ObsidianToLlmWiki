from __future__ import annotations

import unittest
from pathlib import Path

from tests.test_support import load_script_module


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "00_system" / "scripts"
wiki_lib = load_script_module(SCRIPT_DIR / "wiki_lib.py", "wiki_lib_governance_test_module")
lint_wiki = load_script_module(SCRIPT_DIR / "lint_wiki.py", "lint_wiki_governance_test_module")
schema_lib = load_script_module(SCRIPT_DIR / "schema_lib.py", "schema_lib_governance_test_module")


class WikiGovernanceTests(unittest.TestCase):
    def test_wikilink_resolution_prefers_the_source_page_sibling(self) -> None:
        project_a = Path("vault/20_projects/active/a/概览.md")
        project_b = Path("vault/20_projects/active/b/概览.md")
        page_map = {
            "20_projects/active/a/概览": project_a,
            "20_projects/active/b/概览": project_b,
        }
        stem_map = {"概览": [project_a, project_b]}

        resolved = wiki_lib.resolve_wikilink(
            "概览",
            "20_projects/active/a/任务.md",
            page_map,
            stem_map,
        )

        self.assertEqual(resolved, project_a)

    def test_wikilink_resolution_uses_the_unique_nearest_project_page(self) -> None:
        project_decision = Path("vault/20_projects/archive/demo/决策.md")
        other_decision = Path("vault/20_projects/active/other/决策.md")
        page_map = {
            "20_projects/archive/demo/决策": project_decision,
            "20_projects/active/other/决策": other_decision,
        }
        stem_map = {"决策": [project_decision, other_decision]}

        resolved = wiki_lib.resolve_wikilink(
            "决策",
            "20_projects/archive/demo/notes/分析.md",
            page_map,
            stem_map,
        )

        self.assertEqual(resolved, project_decision)

    def test_existing_excluded_scaffold_path_is_not_a_dead_link(self) -> None:
        self.assertTrue(
            lint_wiki.direct_wikilink_target_exists(
                "docs/plans/2026-04-17-multimodal-support-plan",
                "20_projects/active/obsidiantowiki/任务.md",
                vault_root=REPO_ROOT,
            )
        )

    def test_generated_health_reports_do_not_pollute_link_health(self) -> None:
        self.assertTrue(
            lint_wiki.should_skip_link_source("40_outputs/analyses/知识库体检-2026-07-16.md")
        )
        self.assertFalse(lint_wiki.should_skip_link_source("20_projects/active/demo/概览.md"))

    def test_historical_and_archived_pages_do_not_create_current_dead_links(self) -> None:
        historical = {
            "rel_path": "20_projects/active/demo/sources/snapshot.md",
            "frontmatter": {"status": "历史"},
        }
        archived = {
            "rel_path": "20_projects/archive/demo/notes/plan.md",
            "frontmatter": {"status": "活跃"},
        }
        active = {
            "rel_path": "20_projects/active/demo/概览.md",
            "frontmatter": {"status": "活跃"},
        }

        self.assertFalse(lint_wiki.should_check_links(historical))
        self.assertFalse(lint_wiki.should_check_links(archived))
        self.assertTrue(lint_wiki.should_check_links(active))

    def test_orphan_check_uses_the_same_current_knowledge_boundary(self) -> None:
        historical = {
            "rel_path": "20_projects/active/demo/sources/snapshot.md",
            "frontmatter": {"status": "历史"},
        }
        archived = {
            "rel_path": "20_projects/archive/demo/概览.md",
            "frontmatter": {"status": "活跃"},
        }
        active = {
            "rel_path": "20_projects/active/demo/概览.md",
            "frontmatter": {"status": "活跃"},
        }

        self.assertFalse(lint_wiki.should_check_orphan(historical))
        self.assertFalse(lint_wiki.should_check_orphan(archived))
        self.assertTrue(lint_wiki.should_check_orphan(active))

    def test_preserved_raw_sources_are_not_treated_as_governed_knowledge_pages(self) -> None:
        raw_source = {
            "rel_path": "01_inbox/raw/original-handbook.md",
            "frontmatter": {},
        }

        self.assertFalse(lint_wiki.should_check_links(raw_source))
        self.assertFalse(lint_wiki.should_check_orphan(raw_source))
        self.assertFalse(schema_lib.page_requires_schema("01_inbox/raw/original-handbook.md"))

    def test_mermaid_node_shapes_are_not_parsed_as_wikilinks(self) -> None:
        body = "before [[real-page]]\n```mermaid\nP1[[[登录页]] 登录页]\n```\nafter"
        stripped = wiki_lib.strip_fenced_code_blocks(body)

        self.assertIn("[[real-page]]", stripped)
        self.assertNotIn("登录页", stripped)

    def test_stale_check_only_tracks_maintained_pages(self) -> None:
        active = {"rel_path": "20_projects/active/demo/概览.md", "frontmatter": {"status": "活跃"}}
        archived = {"rel_path": "20_projects/archive/demo/概览.md", "frontmatter": {"status": "活跃"}}
        snapshot = {
            "rel_path": "20_projects/active/demo/sources/design.md",
            "frontmatter": {"status": "活跃"},
        }
        source = {"rel_path": "01_inbox/clips/source.md", "frontmatter": {"status": "已摄入"}}

        self.assertTrue(lint_wiki.should_check_stale(active))
        self.assertFalse(lint_wiki.should_check_stale(archived))
        self.assertFalse(lint_wiki.should_check_stale(snapshot))
        self.assertFalse(lint_wiki.should_check_stale(source))

    def test_reviewed_date_controls_freshness_without_rewriting_content_date(self) -> None:
        page = {
            "rel_path": "30_shared/prompts/example.md",
            "frontmatter": {
                "status": "常青",
                "updated": "2026-05-19",
                "reviewed": "2026-07-16",
            },
        }

        self.assertEqual(str(lint_wiki.page_freshness_date(page)), "2026-07-16")

    def test_section_backlog_uses_content_date_and_generated_status(self) -> None:
        frontmatter = {
            "type": "章节笔记",
            "status": "已生成",
            "updated": "2026-01-01",
            "recommended_targets": ["review-personal"],
        }

        self.assertTrue(
            lint_wiki.section_requires_promotion_review(
                frontmatter,
                today=lint_wiki.date(2026, 7, 16),
                backlog_days=30,
            )
        )
        frontmatter["status"] = "已提升"
        self.assertFalse(
            lint_wiki.section_requires_promotion_review(
                frontmatter,
                today=lint_wiki.date(2026, 7, 16),
                backlog_days=30,
            )
        )

    def test_scaffold_guides_and_generated_views_are_schema_exempt(self) -> None:
        self.assertFalse(schema_lib.page_requires_schema("快速开始.md"))
        self.assertFalse(schema_lib.page_requires_schema("标准自然语言话术清单.md"))
        self.assertFalse(schema_lib.page_requires_schema("40_outputs/学习候选审批视图.md"))
        self.assertTrue(schema_lib.page_requires_schema("30_shared/prompts/自然语言启动指令.md"))

    def test_schema_rejects_domains_outside_the_four_knowledge_layers(self) -> None:
        page = {
            "rel_path": "30_shared/patterns/example.md",
            "frontmatter": {
                "title": "Example",
                "type": "模式",
                "domain": "shared",
                "status": "常青",
                "updated": "2026-07-16",
                "summary": "Example.",
            },
        }
        registry = {
            "default_required": ["title", "type", "domain", "status", "updated", "summary"],
            "allowed_domains": ["个人", "项目", "共享", "输出"],
            "type_rules": {},
        }

        errors = schema_lib.validate_page_schema(page, registry)

        self.assertTrue(any("domain" in error and "shared" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
