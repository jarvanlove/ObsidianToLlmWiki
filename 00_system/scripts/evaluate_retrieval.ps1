param(
    [Parameter(Mandatory = $true)][string]$用例,
    [string]$索引路径 = "",
    [double]$最低通过率 = 1.0,
    [double]$最低MRR = 0.8,
    [ValidateSet("text", "json")][string]$格式 = "text"
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonScript = Join-Path $scriptDir "evaluate_retrieval.py"
$argsList = @(
    "--cases", $用例,
    "--minimum-pass-rate", $最低通过率,
    "--minimum-mrr", $最低MRR,
    "--format", $格式
)
if ($索引路径 -ne "") { $argsList += @("--index-path", $索引路径) }

python $pythonScript @argsList
