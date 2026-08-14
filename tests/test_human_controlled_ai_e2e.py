from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "00_system" / "scripts"
OTW = SCRIPTS / "otw.py"
HANDLER = SCRIPTS / "handle_nl_request.py"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from context_integrity import inspect_page  # noqa: E402
from engineering_governance import (  # noqa: E402
    build_explanation_package,
    capture_git_baseline,
    classify_risk,
    create_task_state,
    evaluate_scope,
    evaluate_understanding_gate,
    load_task_state,
    record_capability_observation,
    record_human_understanding,
    record_task_contract,
    save_task_state,
    set_task_risk,
    set_task_scope,
    transition_task,
)
from migrate_project_memory import CORE_PAGE_NAMES, migrate_project_memory  # noqa: E402
from project_cockpit import build_cockpit  # noqa: E402
from project_session import build_receipt  # noqa: E402
from wiki_lib import parse_frontmatter  # noqa: E402


def run(*args: str, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args), cwd=cwd, env=env, check=False, capture_output=True, text=True, encoding="utf-8"
    )


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return run("git", *args, cwd=repo)


def evidence() -> list[dict[str, object]]:
    return [{
        "kind": "acceptance",
        "command": "python -m unittest tests.test_human_controlled_ai_e2e -v",
        "exit_code": 0,
        "result": "passed",
        "recorded_at": datetime.now().astimezone().replace(microsecond=0).isoformat(),
        "source": "deterministic",
    }]


class HumanControlledAiE2ETests(unittest.TestCase):
    def environment(self, home: Path) -> dict[str, str]:
        env = os.environ.copy()
        env.update({"HOME": str(home), "USERPROFILE": str(home), "PYTHONIOENCODING": "utf-8"})
        return env

    def attach(self, root: Path, slug: str = "demo") -> tuple[Path, Path, dict[str, str]]:
        repo, vault, home = root / "repo", root / "vault", root / "home"
        repo.mkdir()
        vault.mkdir()
        home.mkdir()
        env = self.environment(home)
        for args in (("init",), ("config", "user.email", "test@example.com"), ("config", "user.name", "Test")):
            self.assertEqual(git(repo, *args).returncode, 0)
        attached = run(
            sys.executable, str(OTW), "start", "--repo-root", str(repo), "--wiki-root", str(vault),
            cwd=REPO_ROOT, env=env,
        )
        self.assertEqual(attached.returncode, 0, attached.stderr)
        return repo, vault, env

    def request(self, repo: Path, env: dict[str, str], text: str) -> subprocess.CompletedProcess[str]:
        return run(
            sys.executable, str(HANDLER), "--repo-root", str(repo), "--request", text,
            cwd=REPO_ROOT, env=env,
        )

    def test_a_b_c_normal_repair_starts_but_scope_and_unknown_root_cause_block(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo, _, env = self.attach(Path(temp))
            started = self.request(repo, env, "修复导出失败")
            self.assertEqual(started.returncode, 0, started.stderr)
            self.assertTrue((repo / ".obsidiantowiki" / "task-state.json").exists())

            set_task_scope(repo, ["src/export.py"])
            drift = evaluate_scope(repo, ["src/export.py", "src/auth/session.py"])
            self.assertTrue(drift["blocking"])
            self.assertEqual(drift["action"], "replan")

            diagnosis_repo = Path(temp) / "diagnosis"
            diagnosis_repo.mkdir()
            create_task_state(diagnosis_repo, "Fix export failure", "bug_fix")
            record_task_contract(diagnosis_repo, reproduction="Export returns 500.")
            with self.assertRaisesRegex(ValueError, "root_cause"):
                transition_task(diagnosis_repo, "planned", reason="attempt implementation without diagnosis")

    def test_d_e_p1_requires_human_understanding_and_capability_stays_personal(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            create_task_state(repo, "修复登录认证失败", "bug_fix")
            set_task_risk(repo, classify_risk("修复登录认证失败"))
            record_task_contract(
                repo,
                reproduction="Expired session returns 500.",
                root_cause="The expired-session branch skips validation.",
                minimal_fix="Restore validation in that branch only.",
                acceptance=["Expired sessions return 401."],
            )
            package = build_explanation_package(repo, changed_files=["src/auth/session.py"], evidence=evidence())
            self.assertEqual(evaluate_understanding_gate(repo, package, risk_level="P1")["status"], "blocked")

            record_human_understanding(
                repo,
                package,
                confirmed_by="product-owner",
                understood_impact_and_remaining_risks=True,
                confirmation_source="human",
            )
            observation = record_capability_observation(
                repo,
                topic="authentication/session boundary",
                observation_kind="risk_boundary_identified",
                observation="User identified the authentication boundary before reveal.",
                evidence_ref="session-receipt.json#evidence-0",
            )
            receipt = build_receipt(repo, {
                "task": load_task_state(repo)["task"],
                "task_id": load_task_state(repo)["task_id"],
                "risk": {"level": "P1"},
                "evidence": evidence(),
                "changed_files": ["src/auth/session.py"],
                "control_file_update_candidates": [],
                "wiki_file_back_candidates": [],
            })
            summary_path = repo / ".obsidiantowiki" / "pilot-summary.json"
            summary_path.parent.mkdir(exist_ok=True)
            summary_path.write_text(json.dumps({
                "pilot": "simulated-p1-authentication",
                "risk": receipt["risk"],
                "understanding": receipt["gate_results"]["human_understanding"]["status"],
                "capability_destination": observation["destination"],
            }, ensure_ascii=False, indent=2), encoding="utf-8")
            self.assertEqual(evaluate_understanding_gate(repo, package, risk_level="P1")["status"], "passed")
            self.assertEqual(observation["destination"], "personal")
            self.assertFalse(any(item.get("suggested_destination") == "shared" for item in receipt["knowledge_candidates"]))
            self.assertTrue(summary_path.exists())
            self.assertNotIn("secret", summary_path.read_text(encoding="utf-8").lower())

    def test_f_interrupted_task_preserves_preexisting_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            self.assertEqual(git(repo, "init").returncode, 0)
            git(repo, "config", "user.email", "test@example.com")
            git(repo, "config", "user.name", "Test")
            (repo / ".gitignore").write_text(".obsidiantowiki/\n", encoding="utf-8")
            (repo / "existing.txt").write_text("initial\n", encoding="utf-8")
            git(repo, "add", ".gitignore", "existing.txt")
            git(repo, "commit", "-m", "initial")
            (repo / "existing.txt").write_text("user work\n", encoding="utf-8")
            state = create_task_state(repo, "Add governed feature", "code_change")
            state["baseline"] = capture_git_baseline(repo)
            save_task_state(repo, state)
            (repo / "feature.py").write_text("enabled = True\n", encoding="utf-8")

            comparison = evaluate_scope(repo, ["feature.py"])
            saved = load_task_state(repo)
            summary_path = repo / ".obsidiantowiki" / "pilot-summary.json"
            summary_path.write_text(json.dumps({
                "pilot": "preexisting-dirty-worktree",
                "preexisting": saved["baseline"]["tracked_modified"],
                "task_changes": comparison["changed"],
                "task_id": saved["task_id"],
            }, ensure_ascii=False, indent=2), encoding="utf-8")
            self.assertEqual(saved["baseline"]["tracked_modified"], ["existing.txt"])
            self.assertIn("feature.py", comparison["changed"])
            self.assertEqual((repo / "existing.txt").read_text(encoding="utf-8"), "user work\n")
            self.assertTrue(summary_path.exists())

    def test_g_h_empty_and_large_legacy_projects_create_reviewable_atomic_memory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            empty_root = root / "empty"
            empty_root.mkdir()
            empty_repo, empty_vault, _ = self.attach(empty_root)
            empty_context = json.loads((empty_repo / "wiki.context.json").read_text(encoding="utf-8"))
            empty_project = empty_vault / "20_projects" / "active" / empty_context["project_slug"]
            for name in CORE_PAGE_NAMES:
                (empty_project / name).write_text(
                    f"---\ntitle: {name[:-3]}\nproject: {empty_context['project_slug']}\n---\n# {name[:-3]}\n\n待补充。\n",
                    encoding="utf-8",
                )
            (empty_repo / "PRODUCT_SPEC.md").write_text("# Product\n\nControlled AI workflow.\n", encoding="utf-8")
            initial = migrate_project_memory(empty_repo, apply=True, today=date(2026, 8, 14))
            initial_cards = list((empty_project / "memory").glob("CONTROL-*.md"))
            self.assertEqual(initial["classification"], "template")
            self.assertTrue(initial_cards)
            self.assertTrue(all(parse_frontmatter(path.read_text(encoding="utf-8"))[0]["status"] == "pending_review" for path in initial_cards))

            legacy_root = root / "legacy"
            legacy_root.mkdir()
            repo, vault, _ = self.attach(legacy_root)
            context = json.loads((repo / "wiki.context.json").read_text(encoding="utf-8"))
            project = vault / "20_projects" / "active" / context["project_slug"]
            for name in CORE_PAGE_NAMES:
                (project / name).write_text(
                    f"---\ntitle: {name[:-3]}\nproject: {context['project_slug']}\n---\n# {name[:-3]}\n\n" + "legacy " * 22000,
                    encoding="utf-8",
                )

            migrated = migrate_project_memory(repo, apply=True, today=date(2026, 8, 14))
            cards = list((project / "memory").glob("LEGACY-*.md"))
            self.assertEqual(migrated["classification"], "long")
            self.assertEqual(migrated["status"], "applied")
            self.assertEqual(len(cards), 7)
            self.assertTrue(all(parse_frontmatter(path.read_text(encoding="utf-8"))[0]["status"] == "pending_review" for path in cards))
            self.assertTrue(Path(migrated["manifest"]).exists())

    def test_i_j_damaged_context_is_excluded_while_natural_language_cockpit_remains_available(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo, vault, env = self.attach(Path(temp))
            context = json.loads((repo / "wiki.context.json").read_text(encoding="utf-8"))
            memory = vault / context["project_memory"]
            memory.write_text("---\ntitle: Broken\n", encoding="utf-8")
            policy = {
                "required_fields": ["title", "type", "domain", "status", "updated", "summary"],
                "provenance_fields": ["source_refs"],
                "default_max_age_days": 30,
                "vault_root": str(vault),
                "private_policy": {"ai_access": {"excluded_paths": [], "excluded_globs": []}},
            }
            integrity = inspect_page(memory, policy=policy, today=date(2026, 8, 14))
            cockpit = build_cockpit(repo)
            answer = self.request(repo, env, "项目现在怎么样")
            self.assertEqual(integrity["status"], "quarantined")
            self.assertNotIn("Broken", json.dumps(cockpit, ensure_ascii=False))
            self.assertEqual(answer.returncode, 0, answer.stderr)
            self.assertIn("当前状态", answer.stdout)
            self.assertTrue(Path(cockpit["html_path"]).exists())

    def test_boundaries_read_only_creates_nothing_and_unattached_mutation_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, home = root / "repo", root / "home"
            repo.mkdir()
            home.mkdir()
            env = self.environment(home)
            read_only = self.request(repo, env, "解释这段代码")
            mutation = self.request(repo, env, "修改首页按钮间距")

        self.assertEqual(read_only.returncode, 0)
        self.assertFalse((repo / ".obsidiantowiki" / "task-state.json").exists())
        self.assertNotEqual(mutation.returncode, 0)
        self.assertIn("尚未接入 wiki", mutation.stderr)

    def test_release_entry_docs_start_with_the_four_user_promises(self) -> None:
        requirements = {
            "README.md": ("接入一次", "根因", "自动记录", "开始工作"),
            "README-zh.md": ("接入一次", "根因", "自动记录", "开始工作"),
            "README-EN.md": ("Attach once", "root cause", "automatically", "start work"),
            "快速开始.md": ("接入一次", "根因", "自动记录", "开始工作"),
            "使用手册.md": ("接入一次", "根因", "自动记录", "开始工作"),
            "标准自然语言话术清单.md": ("接入一次", "根因", "自动记录", "开始工作"),
        }
        for name, required in requirements.items():
            with self.subTest(name=name):
                opening = "\n".join((REPO_ROOT / name).read_text(encoding="utf-8").splitlines()[:35])
                for phrase in required:
                    self.assertIn(phrase, opening)


if __name__ == "__main__":
    unittest.main()
