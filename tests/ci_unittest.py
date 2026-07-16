from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path


def workflow_escape(value: str) -> str:
    return value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))
suite = unittest.defaultTestLoader.discover(str(repo_root / "tests"))
result = unittest.TextTestRunner(verbosity=2).run(suite)

if not result.wasSuccessful() and os.environ.get("GITHUB_ACTIONS") == "true":
    for test, traceback in [*result.failures, *result.errors]:
        detail = workflow_escape(f"{test}\n{traceback}"[:12000])
        print(f"::error title=Unit test failure::{detail}")

raise SystemExit(0 if result.wasSuccessful() else 1)
