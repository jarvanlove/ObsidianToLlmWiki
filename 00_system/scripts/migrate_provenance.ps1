param(
    [switch]$应用,
    [string[]]$路径 = @(),
    [ValidateSet("text", "json")][string]$格式 = "text"
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonScript = Join-Path $scriptDir "migrate_provenance.py"
$argsList = @("--format", $格式)
if ($应用) { $argsList += "--apply" }
foreach ($item in $路径) { $argsList += @("--path", $item) }

python $pythonScript @argsList
