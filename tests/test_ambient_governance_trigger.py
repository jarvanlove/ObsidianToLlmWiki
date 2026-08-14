from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "00_system" / "scripts"
HANDLER = SCRIPTS / "handle_nl_request.py"
ATTACH = SCRIPTS / "attach_project.py"
sys.path.insert(0, str(SCRIPTS))

from handle_nl_request import classify_engineering_intent, classify_request  # noqa: E402


class AmbientGovernanceTriggerTests(unittest.TestCase):
    def _environment(self, home: Path) -> dict[str, str]:
        env = os.environ.copy()
        env.update({"HOME": str(home), "USERPROFILE": str(home), "PYTHONIOENCODING": "utf-8"})
        return env

    def _attach(self, root: Path) -> tuple[Path, dict[str, str]]:
        repo = root / "project"
        vault = root / "vault"
        home = root / "home"
        repo.mkdir()
        vault.mkdir()
        home.mkdir()
        env = self._environment(home)
        subprocess.run(["git", "init"], cwd=repo, env=env, check=True, capture_output=True)
        attached = subprocess.run(
            [sys.executable, str(ATTACH), "--repo-root", str(repo), "--project", "project", "--wiki-root", str(vault)],
            cwd=REPO_ROOT,
            env=env,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(attached.returncode, 0, attached.stderr)
        return repo, env

    def _request(self, repo: Path, env: dict[str, str], request: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(HANDLER), "--repo-root", str(repo), "--request", request],
            cwd=REPO_ROOT,
            env=env,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_intent_classification_preserves_explicit_commands(self) -> None:
        self.assertEqual(classify_engineering_intent("解释这段代码"), "read_only")
        self.assertEqual(classify_engineering_intent("为什么要修改这个函数"), "read_only")
        self.assertEqual(classify_engineering_intent("修复登录失败"), "code_change")
        self.assertEqual(classify_engineering_intent("做一个登录页面"), "code_change")
        self.assertEqual(classify_engineering_intent("部署到生产"), "external_mutation")
        self.assertEqual(classify_engineering_intent("删除生产数据"), "destructive")
        self.assertEqual(classify_request("开始工作"), "start_work")
        self.assertEqual(classify_request("继续"), "continue_work")
        self.assertEqual(classify_request("收工"), "close_work")

    def test_read_only_request_does_not_create_a_task(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "project"
            home = root / "home"
            repo.mkdir()
            home.mkdir()
            result = self._request(repo, self._environment(home), "解释这段代码")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "治理未创建任务 · read_only")
            self.assertFalse((repo / ".obsidiantowiki/task-state.json").exists())

    def test_code_change_creates_and_existing_task_resumes_without_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo, env = self._attach(Path(temp))
            created = self._request(repo, env, "修复登录失败")
            self.assertEqual(created.returncode, 0, created.stderr)
            state_path = repo / ".obsidiantowiki/task-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["task"], "修复登录失败")
            self.assertEqual(state["intent"], "code_change")
            self.assertEqual(state["risk"]["level"], "P1")
            self.assertIsNone(state["risk"]["confirmed_by"])
            self.assertIn("治理需确认", created.stdout)

            resumed = self._request(repo, env, "修改首页按钮间距")
            self.assertEqual(resumed.returncode, 0, resumed.stderr)
            resumed_state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(resumed_state["task_id"], state["task_id"])
            self.assertEqual(resumed_state["task"], "修复登录失败")
            self.assertIn("治理已恢复", resumed.stdout)

    def test_normal_p2_change_is_one_line_and_unattached_change_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            unattached = root / "unattached"
            home = root / "unattached-home"
            unattached.mkdir()
            home.mkdir()
            blocked = self._request(unattached, self._environment(home), "修改首页按钮间距")
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn("当前项目尚未接入 wiki", blocked.stderr)
            self.assertFalse((unattached / ".obsidiantowiki/task-state.json").exists())

        with tempfile.TemporaryDirectory() as temp:
            repo, env = self._attach(Path(temp))
            created = self._request(repo, env, "修改首页按钮间距")
            self.assertEqual(created.returncode, 0, created.stderr)
            self.assertEqual(len(created.stdout.strip().splitlines()), 1)
            self.assertIn("治理已启动", created.stdout)
            self.assertIn("· P2 ·", created.stdout)

    def test_external_and_destructive_requests_stop_at_required_gate(self) -> None:
        scenarios = [
            ("部署到生产", "external_mutation", "P1", "治理需确认"),
            ("删除生产数据", "destructive", "P0", "治理需授权"),
        ]
        for request, intent, risk, message in scenarios:
            with self.subTest(request=request), tempfile.TemporaryDirectory() as temp:
                repo, env = self._attach(Path(temp))
                result = self._request(repo, env, request)
                self.assertEqual(result.returncode, 0, result.stderr)
                state = json.loads((repo / ".obsidiantowiki/task-state.json").read_text(encoding="utf-8"))
                self.assertEqual(state["intent"], intent)
                self.assertEqual(state["risk"]["level"], risk)
                self.assertIsNone(state["risk"]["confirmed_by"])
                self.assertEqual(state["status"], "investigating")
                self.assertIn(message, result.stdout)


if __name__ == "__main__":
    unittest.main()
