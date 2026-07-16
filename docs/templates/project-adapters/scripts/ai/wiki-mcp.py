from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTEXT_PATH = REPO_ROOT / "wiki.context.json"


def main() -> None:
    if not CONTEXT_PATH.exists():
        raise SystemExit("wiki.context.json is missing; attach this project to ObsidianToWiki first")
    try:
        context = json.loads(CONTEXT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid wiki.context.json: {exc}") from exc
    wiki_root = Path(str(context.get("wiki_root") or "")).expanduser().resolve()
    server_script = wiki_root / "00_system" / "scripts" / "mcp_retrieval_server.py"
    if not server_script.exists():
        raise SystemExit(f"private wiki MCP runtime is missing: {server_script}")

    env = os.environ.copy()
    env["OBSIDIAN_WIKI_ROOT"] = str(wiki_root)
    env["PYTHONIOENCODING"] = "utf-8"
    completed = subprocess.run([sys.executable, str(server_script)], env=env, check=False)
    raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()
