#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WITH_MCP=0
PROVIDER="all"
PRIVATE_ROOT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --with-mcp) WITH_MCP=1; shift ;;
    --provider) PROVIDER="${2:?--provider requires agents, claude, or all}"; shift 2 ;;
    --private-root) PRIVATE_ROOT="${2:?--private-root requires a path}"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

case "$PROVIDER" in
  agents|claude|all) ;;
  *) echo "Invalid provider: $PROVIDER" >&2; exit 2 ;;
esac

python3 -m venv "$ROOT/.venv"
PYTHON="$ROOT/.venv/bin/python"
"$PYTHON" -m pip install --upgrade pip
"$PYTHON" -m pip install -r "$ROOT/00_system/requirements.txt"
if [[ "$WITH_MCP" -eq 1 ]]; then
  "$PYTHON" -m pip install -r "$ROOT/00_system/requirements-mcp.txt"
fi

SETUP_ARGS=("$ROOT/00_system/scripts/otw.py" setup --provider "$PROVIDER")
if [[ -n "$PRIVATE_ROOT" ]]; then
  SETUP_ARGS+=(--private-root "$PRIVATE_ROOT")
fi
"$PYTHON" "${SETUP_ARGS[@]}"
