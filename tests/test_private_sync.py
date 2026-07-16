from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYNC_SCRIPT = REPO_ROOT / "00_system" / "scripts" / "sync_private_vault.py"


class PrivateSyncCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.public = root / "public"
        self.private = root / "private"
        self.public.mkdir()
        self.private.mkdir()

        self.env = os.environ.copy()
        self.env["OBSIDIAN_WIKI_ROOT"] = str(self.public)
        self.env["PYTHONIOENCODING"] = "utf-8"

        manifest = {
            "categories": {
                "root": ["README.md"],
                "system": [
                    "00_system/scripts",
                    "00_system/registry/page_schemas.json",
                    "00_system/registry/private_sync_manifest.json",
                ],
                "prompts": ["30_shared/prompts"],
            },
            "ignore_globs": ["**/__pycache__/**", "**/.cache/**", "**/*.sqlite3"],
            "protected_globs": [
                "Home.md",
                "index.md",
                "log.md",
                "00_system/registry/projects.json",
                "30_shared/architectures/**",
                "30_shared/索引.md",
            ],
        }
        registry = self.public / "00_system" / "registry"
        registry.mkdir(parents=True)
        (registry / "private_sync_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (registry / "page_schemas.json").write_text("{}\n", encoding="utf-8")
        (registry / "projects.json").write_text('{"public": true}\n', encoding="utf-8")

        scripts = self.public / "00_system" / "scripts"
        scripts.mkdir(parents=True)
        (scripts / "tool.py").write_text("print('new')\n", encoding="utf-8")
        cache = self.public / "00_system" / ".cache"
        cache.mkdir(parents=True)
        (cache / "retrieval.sqlite3").write_bytes(b"not-a-real-db")

        (self.public / "README.md").write_text("new readme\n", encoding="utf-8")
        (self.public / "Home.md").write_text("public home\n", encoding="utf-8")
        (self.public / "index.md").write_text("public index\n", encoding="utf-8")
        public_shared = self.public / "30_shared"
        (public_shared / "architectures").mkdir(parents=True)
        (public_shared / "prompts").mkdir(parents=True)
        (public_shared / "architectures" / "private.md").write_text("public architecture\n", encoding="utf-8")
        (public_shared / "prompts" / "managed.md").write_text("public prompt\n", encoding="utf-8")
        (public_shared / "索引.md").write_text("public shared index\n", encoding="utf-8")

        private_registry = self.private / "00_system" / "registry"
        private_registry.mkdir(parents=True)
        (private_registry / "projects.json").write_text('{"private": true}\n', encoding="utf-8")
        (self.private / "Home.md").write_text("private home\n", encoding="utf-8")
        (self.private / "index.md").write_text("private index\n", encoding="utf-8")
        (self.private / "README.md").write_text("old readme\n", encoding="utf-8")
        private_shared = self.private / "30_shared"
        (private_shared / "architectures").mkdir(parents=True)
        (private_shared / "architectures" / "private.md").write_text("private architecture\n", encoding="utf-8")
        (private_shared / "索引.md").write_text("private shared index\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def run_sync(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SYNC_SCRIPT),
                "--source-root",
                str(self.public),
                "--private-root",
                str(self.private),
                "--format",
                "json",
                *args,
            ],
            cwd=REPO_ROOT,
            env=self.env,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_default_sync_creates_missing_files_and_stages_unproven_conflicts(self) -> None:
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)

        self.assertEqual((self.private / "README.md").read_text(encoding="utf-8"), "old readme\n")
        self.assertEqual(
            (self.private / "40_outputs/upgrade-candidates/private-scaffold/README.md.new").read_text(encoding="utf-8"),
            "new readme\n",
        )
        self.assertTrue((self.private / "00_system" / "scripts" / "tool.py").exists())
        self.assertEqual((self.private / "Home.md").read_text(encoding="utf-8"), "private home\n")
        self.assertEqual((self.private / "index.md").read_text(encoding="utf-8"), "private index\n")
        self.assertEqual(
            (self.private / "00_system" / "registry" / "projects.json").read_text(encoding="utf-8"),
            '{"private": true}\n',
        )
        self.assertFalse((self.private / "00_system" / ".cache").exists())
        self.assertEqual(
            (self.private / "30_shared" / "architectures" / "private.md").read_text(encoding="utf-8"),
            "private architecture\n",
        )
        self.assertEqual((self.private / "30_shared" / "索引.md").read_text(encoding="utf-8"), "private shared index\n")
        self.assertEqual(
            (self.private / "30_shared" / "prompts" / "managed.md").read_text(encoding="utf-8"),
            "public prompt\n",
        )
        self.assertGreater(payload["summary"]["created"], 0)
        self.assertEqual(payload["summary"]["updated"], 0)
        self.assertEqual(payload["summary"]["conflict_staged"], 1)

    def test_second_sync_reports_identical_files_as_skipped(self) -> None:
        first = self.run_sync()
        self.assertEqual(first.returncode, 0, first.stderr)

        second = self.run_sync()
        self.assertEqual(second.returncode, 0, second.stderr)
        payload = json.loads(second.stdout)

        self.assertEqual(payload["summary"]["created"], 0)
        self.assertEqual(payload["summary"]["updated"], 0)
        self.assertGreater(payload["summary"]["skipped"], 0)
        self.assertEqual(payload["summary"]["conflict_staged"], 1)

    def test_recorded_unchanged_baseline_allows_a_safe_update(self) -> None:
        (self.public / "README.md").write_text("old readme\n", encoding="utf-8")
        baseline = self.run_sync("--record-baseline", "--path", "README.md")
        self.assertEqual(baseline.returncode, 0, baseline.stderr)
        self.assertEqual(json.loads(baseline.stdout)["summary"]["baseline_recorded"], 1)

        (self.public / "README.md").write_text("new readme\n", encoding="utf-8")
        updated = self.run_sync("--path", "README.md")
        self.assertEqual(updated.returncode, 0, updated.stderr)
        self.assertEqual(json.loads(updated.stdout)["summary"]["updated"], 1)
        self.assertEqual((self.private / "README.md").read_text(encoding="utf-8"), "new readme\n")

    def test_baseline_accepts_only_line_ending_differences_for_text_files(self) -> None:
        script = self.public / "00_system/scripts/tool.py"
        script.write_text("print('old')\n", encoding="utf-8", newline="\n")
        private_script = self.private / "00_system/scripts/tool.py"
        private_script.parent.mkdir(parents=True, exist_ok=True)
        private_script.write_text("print('old')\r\n", encoding="utf-8", newline="")
        baseline = self.run_sync("--record-baseline", "--path", "00_system/scripts/tool.py")
        self.assertEqual(baseline.returncode, 0, baseline.stderr)
        self.assertEqual(json.loads(baseline.stdout)["summary"]["baseline_recorded"], 1)

        script.write_text("print('new')\n", encoding="utf-8", newline="\n")
        updated = self.run_sync("--path", "00_system/scripts/tool.py")
        self.assertEqual(updated.returncode, 0, updated.stderr)
        self.assertEqual(json.loads(updated.stdout)["summary"]["updated"], 1)

    def test_initialize_creates_a_missing_private_root(self) -> None:
        missing = Path(self.temp_dir.name) / "new-private"
        result = subprocess.run(
            [
                sys.executable,
                str(SYNC_SCRIPT),
                "--source-root",
                str(self.public),
                "--private-root",
                str(missing),
                "--initialize",
                "--format",
                "json",
            ],
            cwd=REPO_ROOT,
            env=self.env,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((missing / "README.md").exists())
        self.assertTrue((missing / "00_system/registry/private_scaffold_state.json").exists())

    def test_path_scope_is_precise_and_protected_paths_are_rejected(self) -> None:
        precise = self.run_sync("--path", "README.md")
        self.assertEqual(precise.returncode, 0, precise.stderr)
        self.assertFalse((self.private / "00_system" / "scripts" / "tool.py").exists())
        self.assertEqual((self.private / "README.md").read_text(encoding="utf-8"), "old readme\n")

        protected = self.run_sync("--path", "00_system/registry/projects.json")
        self.assertNotEqual(protected.returncode, 0)
        self.assertIn("protected", protected.stderr.lower())
        self.assertEqual(
            (self.private / "00_system" / "registry" / "projects.json").read_text(encoding="utf-8"),
            '{"private": true}\n',
        )


if __name__ == "__main__":
    unittest.main()
