param(
    [switch]$WithMcp,
    [ValidateSet("agents", "claude", "all")][string]$Provider = "all",
    [string]$PrivateRoot = ""
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
$SetupArgs = @("$Root\00_system\scripts\otw.py", "setup", "--provider", $Provider)
if (-not [string]::IsNullOrWhiteSpace($PrivateRoot)) {
    $SetupArgs += @("--private-root", $PrivateRoot)
}
& $Python @SetupArgs
