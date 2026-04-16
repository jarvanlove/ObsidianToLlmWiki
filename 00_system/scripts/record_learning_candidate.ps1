param(
    [Parameter(Mandatory = $true)][string]$标题,
    [Parameter(Mandatory = $true)][string]$观察,
    [string]$原因分析 = "",
    [string]$候选改进 = "",
    [string]$后续验证 = "",
    [string]$项目 = "",
    [string]$标签 = "",
    [string]$摘要 = ""
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonScript = Join-Path $scriptDir "record_learning_candidate.py"

$argsList = @("--title", $标题, "--observation", $观察)
if ($原因分析 -ne "") { $argsList += @("--cause", $原因分析) }
if ($候选改进 -ne "") { $argsList += @("--improvement", $候选改进) }
if ($后续验证 -ne "") { $argsList += @("--validation", $后续验证) }
if ($项目 -ne "") { $argsList += @("--project", $项目) }
if ($标签 -ne "") { $argsList += @("--tags", $标签) }
if ($摘要 -ne "") { $argsList += @("--summary", $摘要) }

python $pythonScript @argsList
