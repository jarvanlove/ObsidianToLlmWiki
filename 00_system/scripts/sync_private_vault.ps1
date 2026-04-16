param(
    [string]$私有库根目录 = "",
    [switch]$仅预览
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonScript = Join-Path $scriptDir "sync_private_vault.py"

$argsList = @()
if ($私有库根目录 -ne "") { $argsList += @("--private-root", $私有库根目录) }
if ($仅预览) { $argsList += "--dry-run" }

python $pythonScript @argsList
