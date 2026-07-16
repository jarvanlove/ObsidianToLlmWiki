#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -m venv "$ROOT/.venv"
PYTHON="$ROOT/.venv/bin/python"
"$PYTHON" -m pip install --upgrade pip
"$PYTHON" -m pip install -r "$ROOT/00_system/requirements.txt"
if [[ "${1:-}" == "--with-mcp" ]]; then
  "$PYTHON" -m pip install -r "$ROOT/00_system/requirements-mcp.txt"
fi
"$PYTHON" "$ROOT/00_system/scripts/install_manager_skill.py" --provider all
"$PYTHON" "$ROOT/00_system/scripts/doctor.py"
