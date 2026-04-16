param(
    [Parameter(Mandatory = $true)][string]$标题,
    [Parameter(Mandatory = $true)][string]$问题,
    [Parameter(Mandatory = $true)][string]$结论,
    [string]$项目 = "",
    [string]$标签 = "",
    [string]$摘要 = "",
    [string]$证据 = "",
    [string]$后续动作 = ""
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonScript = Join-Path $scriptDir "file_back_query.py"

$argsList = @("--title", $标题, "--question", $问题, "--conclusion", $结论)
if ($项目 -ne "") { $argsList += @("--project", $项目) }
if ($标签 -ne "") { $argsList += @("--tags", $标签) }
if ($摘要 -ne "") { $argsList += @("--summary", $摘要) }
if ($证据 -ne "") { $argsList += @("--evidence", $证据) }
if ($后续动作 -ne "") { $argsList += @("--follow-up", $后续动作) }

python $pythonScript @argsList
