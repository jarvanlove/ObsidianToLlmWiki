from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_SCRIPT = REPO_ROOT / "00_system" / "scripts" / "mcp_retrieval_server.py"
ADAPTER_ROOT = REPO_ROOT / "docs" / "templates" / "project-adapters"


def compatible_mcp_sdk() -> bool:
    return importlib.util.find_spec("mcp") is not None


class AgentRetrievalAdapterTests(unittest.TestCase):
    def test_project_templates_include_provider_thin_skills(self) -> None:
        skill_paths = [
            ADAPTER_ROOT / ".agents" / "skills" / "obsidiantowiki-retrieval" / "SKILL.md",
            ADAPTER_ROOT / ".claude" / "skills" / "obsidiantowiki-retrieval" / "SKILL.md",
        ]
        for skill_path in skill_paths:
            self.assertTrue(skill_path.exists(), skill_path)
            content = skill_path.read_text(encoding="utf-8")
            self.assertIn("wiki-search.py", content)
            self.assertNotIn("C:\\Work", content)

    @unittest.skipUnless(compatible_mcp_sdk(), "optional MCP SDK dependencies are not compatible")
    def test_mcp_stdio_exposes_structured_search_and_context_tools(self) -> None:
        from mcp.shared.version import LATEST_PROTOCOL_VERSION

        def exercise_server(vault: Path) -> None:
            env = os.environ.copy()
            env["OBSIDIAN_WIKI_ROOT"] = str(vault)
            env["PYTHONIOENCODING"] = "utf-8"
            messages = [
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": LATEST_PROTOCOL_VERSION,
                        "capabilities": {},
                        "clientInfo": {"name": "otw-test", "version": "1"},
                    },
                },
                {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
                {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {"name": "search_wiki", "arguments": {"query": "检索契约", "limit": 2}},
                },
                {
                    "jsonrpc": "2.0",
                    "id": 4,
                    "method": "tools/call",
                    "params": {
                        "name": "get_wiki_context",
                        "arguments": {"query": "检索契约", "token_budget": 220},
                    },
                },
            ]
            input_text = "".join(
                json.dumps(message, ensure_ascii=False, separators=(",", ":")) + "\n"
                for message in messages
            )
            completed = subprocess.run(
                [sys.executable, str(SERVER_SCRIPT)],
                cwd=REPO_ROOT,
                env=env,
                input=input_text,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=60,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            responses = {item["id"]: item for item in map(json.loads, completed.stdout.splitlines()) if "id" in item}

            names = {tool["name"] for tool in responses[2]["result"]["tools"]}
            self.assertEqual(names, {"search_wiki", "get_wiki_context"})
            structured = responses[3]["result"]["structuredContent"]
            self.assertEqual(structured["results"][0]["path"], "30_shared/检索契约.md")
            self.assertIn("OTW Context Pack", responses[4]["result"]["content"][0]["text"])

        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            shared = vault / "30_shared"
            shared.mkdir()
            (shared / "检索契约.md").write_text(
                "---\n"
                "title: 检索契约\n"
                "type: 架构\n"
                "domain: 共享\n"
                "status: 常青\n"
                "updated: 2026-07-16\n"
                "summary: 面向智能体的检索契约。\n"
                "tags: []\n"
                "---\n\n"
                "# 检索契约\n\n## 稳定输出\n\n返回带出处的 JSON 和 context pack。\n",
                encoding="utf-8",
            )
            exercise_server(vault)


if __name__ == "__main__":
    unittest.main()
