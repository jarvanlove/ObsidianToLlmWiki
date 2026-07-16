param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path "$PSScriptRoot\..\..").Path
$ManagedPython = Join-Path $Root ".venv\Scripts\python.exe"
if (Test-Path $ManagedPython) {
    & $ManagedPython "$PSScriptRoot\otw.py" @Arguments
} else {
    python "$PSScriptRoot\otw.py" @Arguments
}
