from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "00_system" / "scripts"
SEARCH_SCRIPT = SCRIPT_DIR / "search_wiki.py"
BUILD_SCRIPT = SCRIPT_DIR / "build_retrieval_index.py"


def page(
    title: str,
    *,
    page_type: str,
    domain: str,
    project: str = "",
    tags: list[str] | None = None,
    source_refs: list[str] | None = None,
    body: str,
) -> str:
    tags = tags or []
    source_refs = source_refs or []
    project_line = f"project: {project}\n" if project else ""
    tag_lines = "\n".join(f"  - {tag}" for tag in tags) or "  []"
    source_ref_lines = "\n".join(f"  - {ref}" for ref in source_refs) or "  []"
    return (
        "---\n"
        f"title: {title}\n"
        f"type: {page_type}\n"
        f"domain: {domain}\n"
        f"{project_line}"
        "status: 活跃\n"
        "updated: 2026-07-16\n"
        f"summary: {title} 的摘要。\n"
        "tags:\n"
        f"{tag_lines}\n"
        "source_refs:\n"
        f"{source_ref_lines}\n"
        "---\n\n"
        f"# {title}\n\n{body}\n"
    )


class RetrievalCoreCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.vault = Path(self.temp_dir.name)
        self.index_path = self.vault / ".otw-cache" / "retrieval.sqlite3"
        self.env = os.environ.copy()
        self.env["OBSIDIAN_WIKI_ROOT"] = str(self.vault)
        self.env["PYTHONIOENCODING"] = "utf-8"

        (self.vault / "20_projects" / "active" / "demo").mkdir(parents=True)
        (self.vault / "20_projects" / "active" / "other").mkdir(parents=True)
        (self.vault / "30_shared" / "patterns").mkdir(parents=True)

        self.demo_page = self.vault / "20_projects" / "active" / "demo" / "决策.md"
        self.demo_page.write_text(
            page(
                "缓存决策",
                page_type="项目决策",
                domain="项目",
                project="demo",
                tags=["backend", "cache"],
                source_refs=["p.4", "p.5"],
                body="## Redis 取舍\n\n当前项目选择 Redis 保存短期缓存，并保留数据库作为事实源。",
            ),
            encoding="utf-8",
        )
        (self.vault / "20_projects" / "active" / "other" / "决策.md").write_text(
            page(
                "其他项目缓存",
                page_type="项目决策",
                domain="项目",
                project="other",
                tags=["cache"],
                body="## Redis\n\n其他项目也使用 Redis。",
            ),
            encoding="utf-8",
        )
        (self.vault / "30_shared" / "patterns" / "缓存模式.md").write_text(
            page(
                "缓存模式",
                page_type="模式",
                domain="共享",
                tags=["cache"],
                body="## 通用做法\n\nRedis 是可选实现，不应成为业务事实源。",
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def run_script(self, script: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(script), *args],
            cwd=REPO_ROOT,
            env=self.env,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def run_search(self, query: str, *args: str) -> subprocess.CompletedProcess[str]:
        return self.run_script(
            SEARCH_SCRIPT,
            query,
            "--index-path",
            str(self.index_path),
            "--no-log-failures",
            *args,
        )

    def test_build_index_and_json_search_preserve_filters_and_provenance(self) -> None:
        build = self.run_script(BUILD_SCRIPT, "--index-path", str(self.index_path))
        self.assertEqual(build.returncode, 0, build.stderr)
        build_payload = json.loads(build.stdout)
        self.assertEqual(build_payload["schema_version"], 1)
        self.assertEqual(build_payload["indexed_pages"], 3)

        result = self.run_search("Redis", "--project", "demo", "--type", "项目决策", "--format", "json")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)

        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["retrieval"]["backend"], "sqlite-fts5")
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["results"][0]["path"], "20_projects/active/demo/决策.md")
        self.assertEqual(payload["results"][0]["project"], "demo")
        self.assertEqual(payload["results"][0]["source_refs"], ["p.4", "p.5"])
        self.assertEqual(payload["results"][0]["heading"], "Redis 取舍")
        self.assertIn("Redis", payload["results"][0]["snippet"])

    def test_search_refreshes_modified_and_deleted_pages(self) -> None:
        initial = self.run_search("事件溯源", "--format", "json")
        self.assertEqual(initial.returncode, 0, initial.stderr)
        self.assertEqual(json.loads(initial.stdout)["count"], 0)

        self.demo_page.write_text(
            page(
                "缓存决策",
                page_type="项目决策",
                domain="项目",
                project="demo",
                tags=["backend", "cache"],
                body="## 新决策\n\n系统新增事件溯源，用于恢复任务执行状态。",
            ),
            encoding="utf-8",
        )
        modified = self.run_search("事件溯源", "--format", "json")
        self.assertEqual(modified.returncode, 0, modified.stderr)
        modified_payload = json.loads(modified.stdout)
        self.assertEqual(modified_payload["count"], 1)
        self.assertGreaterEqual(modified_payload["retrieval"]["refresh"]["updated"], 1)

        self.demo_page.unlink()
        deleted = self.run_search("事件溯源", "--format", "json")
        self.assertEqual(deleted.returncode, 0, deleted.stderr)
        deleted_payload = json.loads(deleted.stdout)
        self.assertEqual(deleted_payload["count"], 0)
        self.assertEqual(deleted_payload["retrieval"]["refresh"]["deleted"], 1)

    def test_context_pack_is_bounded_and_keeps_source_location(self) -> None:
        result = self.run_search(
            "Redis",
            "--project",
            "demo",
            "--format",
            "context",
            "--token-budget",
            "220",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# OTW Context Pack", result.stdout)
        self.assertIn("20_projects/active/demo/决策.md", result.stdout)
        self.assertIn("p.4", result.stdout)
        self.assertIn("Redis 取舍", result.stdout)
        self.assertLess(len(result.stdout), 1200)

    def test_best_chunk_prefers_query_term_coverage_over_single_fts_term(self) -> None:
        page_path = self.vault / "20_projects" / "active" / "demo" / "架构.md"
        page_path.write_text(
            page(
                "OpenClaw 架构",
                page_type="项目架构",
                domain="项目",
                project="demo",
                body=(
                    "## 来源\n\nOpenClaw 指南。\n\n"
                    "## 核心架构\n\nOpenClaw 架构采用网关、运行时与扩展层。"
                ),
            ),
            encoding="utf-8",
        )

        result = self.run_search("OpenClaw 架构", "--format", "json", "--limit", "1")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["results"][0]["heading"], "核心架构")


if __name__ == "__main__":
    unittest.main()
