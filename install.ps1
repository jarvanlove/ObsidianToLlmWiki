param(
    [switch]$WithMcp,
    [ValidateSet("agents", "claude", "all")][string]$Provider = "all"
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
python -m venv "$Root\.venv"
$Python = "$Root\.venv\Scripts\python.exe"
& $Python -m pip install --upgrade pip
& $Python -m pip install -r "$Root\00_system\requirements.txt"
if ($WithMcp) {
    & $Python -m pip install -r "$Root\00_system\requirements-mcp.txt"
}
& $Python "$Root\00_system\scripts\install_manager_skill.py" --provider $Provider
& $Python "$Root\00_system\scripts\doctor.py"
