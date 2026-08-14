from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

from tests.test_support import load_script_module


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "00_system" / "scripts"
CONTEXT_SCRIPT = SCRIPT_DIR / "context_integrity.py"
OTW_SCRIPT = SCRIPT_DIR / "otw.py"
context_integrity = load_script_module(CONTEXT_SCRIPT, "context_integrity_test_module")
wiki_lib = load_script_module(SCRIPT_DIR / "wiki_lib.py", "wiki_lib_context_integrity_test_module")


def page(
    *,
    page_id: str = "memory-1",
    updated: str = "2026-08-13",
    domain: str = "项目",
    include_summary: bool = True,
    include_source: bool = True,
) -> str:
    fields = [
        "---",
        f"id: {page_id}",
        "title: Trusted memory",
        "type: 项目运行记忆",
        f"domain: {domain}",
        "project: demo",
        "status: 活跃",
        f"updated: {updated}",
    ]
    if include_summary:
        fields.append("summary: Current verified project memory.")
    if include_source:
        fields.extend(["source_refs:", "  - task:task-1"])
    fields.extend(["---", "", "# Trusted memory", "", "Evidence-backed content.", ""])
    return "\n".join(fields)


class ContextIntegrityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.policy = {
            "schema_version": 1,
            "allowed_states": ["trusted", "review_required", "degraded", "quarantined"],
            "required_fields": ["title", "type", "domain", "status", "updated", "summary"],
            "provenance_fields": ["source_receipt", "source_refs", "evidence_refs"],
            "default_max_age_days": 30,
            "vault_root": str(self.root),
            "private_policy": {
                "schema_version": 1,
                "ai_access": {"excluded_paths": [], "excluded_globs": []},
            },
        }
        self.today = date(2026, 8, 13)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def inspect(self, path: Path, **policy_updates: object) -> dict[str, object]:
        policy = dict(self.policy)
        policy.update(policy_updates)
        return context_integrity.inspect_page(path, policy=policy, today=self.today)

    def test_missing_file_is_quarantined(self) -> None:
        result = self.inspect(self.root / "missing.md")
        self.assertEqual(result["status"], "quarantined")
        self.assertEqual(result["reasons"], ["missing_file"])

    def test_invalid_utf8_is_quarantined(self) -> None:
        path = self.root / "invalid.md"
        path.write_bytes(b"---\n\xff\n---\n")
        result = self.inspect(path)
        self.assertEqual(result["status"], "quarantined")
        self.assertEqual(result["reasons"], ["invalid_utf8"])

    def test_unclosed_frontmatter_is_quarantined_and_not_silently_empty(self) -> None:
        path = self.root / "unclosed.md"
        path.write_text("---\ntitle: Broken\n", encoding="utf-8")
        result = self.inspect(path)
        self.assertEqual(result["status"], "quarantined")
        self.assertEqual(result["reasons"], ["frontmatter_unclosed"])
        with self.assertRaises(wiki_lib.FrontmatterError):
            wiki_lib.load_page(path)

    def test_invalid_yaml_is_quarantined(self) -> None:
        path = self.root / "yaml.md"
        path.write_text("---\ntitle: [broken\n---\n\nbody\n", encoding="utf-8")
        result = self.inspect(path)
        self.assertEqual(result["status"], "quarantined")
        self.assertEqual(result["reasons"], ["frontmatter_invalid_yaml"])

    def test_schema_error_is_quarantined(self) -> None:
        path = self.root / "schema.md"
        path.write_text(page(include_summary=False), encoding="utf-8")
        result = self.inspect(path)
        self.assertEqual(result["status"], "quarantined")
        self.assertEqual(result["reasons"], ["schema_missing:summary"])

    def test_schema_domain_mismatch_is_quarantined(self) -> None:
        path = self.root / "domain.md"
        path.write_text(page(domain="个人"), encoding="utf-8")
        policy = dict(self.policy)
        policy["type_rules"] = {"项目运行记忆": {"domain": ["项目"], "required": ["project"]}}
        result = context_integrity.inspect_page(path, policy=policy, today=self.today)
        self.assertEqual(result["status"], "quarantined")
        self.assertEqual(result["reasons"], ["schema_domain:个人"])

    def test_stale_page_is_degraded(self) -> None:
        path = self.root / "stale.md"
        path.write_text(page(updated="2026-06-01"), encoding="utf-8")
        result = self.inspect(path)
        self.assertEqual(result["status"], "degraded")
        self.assertEqual(result["reasons"], ["stale:updated=2026-06-01,max_age_days=30"])

    def test_missing_provenance_requires_review(self) -> None:
        path = self.root / "unproven.md"
        path.write_text(page(include_source=False), encoding="utf-8")
        result = self.inspect(path)
        self.assertEqual(result["status"], "review_required")
        self.assertEqual(result["reasons"], ["missing_provenance"])

    def test_private_policy_exclusion_is_quarantined(self) -> None:
        path = self.root / "private" / "secret.md"
        path.parent.mkdir()
        path.write_text(page(), encoding="utf-8")
        private_policy = {
            "schema_version": 1,
            "ai_access": {"excluded_paths": ["private"], "excluded_globs": []},
        }
        result = self.inspect(path, private_policy=private_policy)
        self.assertEqual(result["status"], "quarantined")
        self.assertEqual(result["reasons"], ["ai_access_excluded"])

    def test_valid_page_is_trusted(self) -> None:
        path = self.root / "trusted.md"
        path.write_text(page(), encoding="utf-8")
        result = self.inspect(path)
        self.assertEqual(result["status"], "trusted")
        self.assertEqual(result["reasons"], [])
        self.assertEqual(result["id"], "memory-1")

    def test_duplicate_ids_quarantine_both_pages(self) -> None:
        first = self.root / "first.md"
        second = self.root / "second.md"
        first.write_text(page(page_id="duplicate"), encoding="utf-8")
        second.write_text(page(page_id="duplicate"), encoding="utf-8")
        required = [
            {"path": str(first), "policy": self.policy},
            {"path": str(second), "policy": self.policy},
        ]
        result = context_integrity.inspect_context(self.root, required)
        self.assertEqual(result["status"], "quarantined")
        self.assertEqual(result["summary"]["quarantined"], 2)
        for inspected in result["pages"]:
            self.assertEqual(inspected["reasons"], ["duplicate_id:duplicate"])

    def test_cli_is_read_only_and_strict_blocks_quarantined_required_page(self) -> None:
        repo = self.root / "repo"
        vault = self.root / "vault"
        memory = vault / "20_projects" / "active" / "demo" / "project.memory.md"
        memory.parent.mkdir(parents=True)
        memory.write_text(page(), encoding="utf-8")
        repo.mkdir()
        (repo / "wiki.context.json").write_text(
            json.dumps(
                {
                    "wiki_root": str(vault),
                    "project_slug": "demo",
                    "project_memory": "20_projects/active/demo/project.memory.md",
                }
            ),
            encoding="utf-8",
        )
        before = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in self.root.rglob("*") if path.is_file()}
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"

        valid = subprocess.run(
            [
                sys.executable,
                str(OTW_SCRIPT),
                "context",
                "check",
                "--repo-root",
                str(repo),
                "--format",
                "json",
                "--strict",
            ],
            cwd=REPO_ROOT,
            env=env,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(valid.returncode, 0, valid.stderr)
        self.assertEqual(json.loads(valid.stdout)["status"], "trusted")
        after = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in self.root.rglob("*") if path.is_file()}
        self.assertEqual(after, before)

        memory.write_text("---\ntitle: Broken\n", encoding="utf-8")
        blocked = subprocess.run(
            [
                sys.executable,
                str(CONTEXT_SCRIPT),
                "--repo-root",
                str(repo),
                "--format",
                "json",
                "--strict",
            ],
            cwd=REPO_ROOT,
            env=env,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(blocked.returncode, 1, blocked.stderr)
        self.assertEqual(json.loads(blocked.stdout)["status"], "quarantined")


if __name__ == "__main__":
    unittest.main()
