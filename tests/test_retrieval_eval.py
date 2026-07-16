from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
EVAL_SCRIPT = REPO_ROOT / "00_system" / "scripts" / "evaluate_retrieval.py"


def page(title: str, heading: str, body: str, *, source_refs: list[str] | None = None) -> str:
    refs = source_refs or []
    ref_lines = "\n".join(f"  - {item}" for item in refs) or "  []"
    return (
        "---\n"
        f"title: {title}\n"
        "type: 架构\n"
        "domain: 共享\n"
        "status: 常青\n"
        "updated: 2026-07-16\n"
        f"summary: {title} 摘要。\n"
        "tags: []\n"
        "source_refs:\n"
        f"{ref_lines}\n"
        "---\n\n"
        f"# {title}\n\n## {heading}\n\n{body}\n"
    )


class RetrievalEvaluationCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.vault = Path(self.temp_dir.name)
        self.env = os.environ.copy()
        self.env["OBSIDIAN_WIKI_ROOT"] = str(self.vault)
        self.env["PYTHONIOENCODING"] = "utf-8"

        content_dir = self.vault / "30_shared" / "architectures"
        content_dir.mkdir(parents=True)
        (content_dir / "同步安全.md").write_text(
            page("同步安全", "保护边界", "私有项目注册表永远不能被 scaffold 同步覆盖。", source_refs=["p.12"]),
            encoding="utf-8",
        )
        (content_dir / "检索契约.md").write_text(
            page("检索契约", "上下文预算", "context pack 必须受 token budget 限制。"),
            encoding="utf-8",
        )

        self.cases_path = self.vault / "retrieval-eval.json"
        self.cases_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "cases": [
                        {
                            "id": "sync-protection",
                            "query": "私有项目注册表 scaffold 覆盖",
                            "expected_paths": ["30_shared/architectures/同步安全.md"],
                            "expected_headings": ["保护边界"],
                            "require_source_refs": True,
                            "max_rank": 1,
                        },
                        {
                            "id": "semantic-probe",
                            "query": "给智能体的有限长度知识包",
                            "expected_paths": ["30_shared/architectures/检索契约.md"],
                            "semantic_probe": True,
                            "gating": False,
                            "max_rank": 1,
                        },
                    ],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def run_eval(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(EVAL_SCRIPT),
                "--cases",
                str(self.cases_path),
                "--index-path",
                str(self.vault / ".cache" / "retrieval.sqlite3"),
                "--format",
                "json",
                "--minimum-pass-rate",
                "1.0",
                "--minimum-mrr",
                "1.0",
            ],
            cwd=REPO_ROOT,
            env=self.env,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_evaluation_enforces_gates_and_reports_semantic_probe_separately(self) -> None:
        result = self.run_eval()
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)

        self.assertEqual(payload["schema_version"], 1)
        self.assertTrue(payload["gate_passed"])
        self.assertEqual(payload["summary"]["gating_pass_rate"], 1.0)
        self.assertEqual(payload["summary"]["mrr"], 1.0)
        gating_case = next(item for item in payload["cases"] if item["id"] == "sync-protection")
        self.assertTrue(gating_case["path_hit"])
        self.assertTrue(gating_case["heading_hit"])
        self.assertTrue(gating_case["provenance_hit"])
        probe = next(item for item in payload["cases"] if item["id"] == "semantic-probe")
        self.assertTrue(probe["semantic_probe"])
        self.assertIn("semantic_retrieval_recommended", payload)


if __name__ == "__main__":
    unittest.main()
