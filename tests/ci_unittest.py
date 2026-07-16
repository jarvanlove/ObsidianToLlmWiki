from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def workflow_escape(value: str) -> str:
    return value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


repo_root = Path(__file__).resolve().parents[1]
process = subprocess.Popen(
    [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
    cwd=repo_root,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    encoding="utf-8",
    errors="replace",
)
output: list[str] = []
assert process.stdout is not None
for line in process.stdout:
    print(line, end="", flush=True)
    output.append(line)
return_code = process.wait()

if return_code and os.environ.get("GITHUB_ACTIONS") == "true":
    detail = workflow_escape("".join(output)[-3500:])
    print(f"::error title=Unit test failure::{detail}")

raise SystemExit(return_code)
