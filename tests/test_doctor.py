from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "00_system" / "scripts" / "doctor.py"


class DoctorTests(unittest.TestCase):
    def test_strict_doctor_passes_for_current_initialized_vault(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            vault = Path(temp)
            registry = vault / "00_system" / "registry"
            registry.mkdir(parents=True)
            (registry / "vault_state.json").write_text(
                json.dumps({"schema_version": 1, "vault_schema_version": 1, "migration_history": []}),
                encoding="utf-8",
            )
            (vault / "wiki.private.json").write_text(
                json.dumps({"schema_version": 1, "ai_access": {"excluded_paths": [], "excluded_globs": []}}),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--repo-root",
                    str(vault),
                    "--wiki-root",
                    str(vault),
                    "--strict",
                    "--format",
                    "json",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "pass")
            self.assertTrue(all(item["status"] == "pass" for item in payload["checks"]))


if __name__ == "__main__":
    unittest.main()
