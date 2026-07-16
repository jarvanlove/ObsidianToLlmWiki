param(
    [string]$私有库根目录 = "",
    [switch]$仅预览,
    [ValidateSet("root", "system", "docs", "prompts")][string[]]$类别 = @(),
    [string[]]$路径 = @(),
    [ValidateSet("text", "json")][string]$格式 = "text"
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonScript = Join-Path $scriptDir "sync_private_vault.py"

$argsList = @()
if ($私有库根目录 -ne "") { $argsList += @("--private-root", $私有库根目录) }
if ($仅预览) { $argsList += "--dry-run" }
foreach ($item in $类别) { $argsList += @("--only", $item) }
foreach ($item in $路径) { $argsList += @("--path", $item) }
$argsList += @("--format", $格式)

python $pythonScript @argsList
