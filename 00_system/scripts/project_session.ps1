param(
    [Parameter(Mandatory = $true)][ValidateSet("check", "start", "close")][string]$命令,
    [string]$项目根目录 = ".",
    [string]$任务 = "",
    [string]$验证结果 = "",
    [string[]]$验证证据 = @(),
    [string]$证据文件 = "",
    [ValidateSet("text", "json", "markdown")][string]$格式 = "text",
    [string]$输出文件 = ""
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonScript = Join-Path $scriptDir "project_session.py"

$argsList = @($命令, "--repo-root", $项目根目录, "--format", $格式)
if ($任务 -ne "") { $argsList += @("--task", $任务) }
if ($验证结果 -ne "") { $argsList += @("--verification", $验证结果) }
foreach ($item in $验证证据) { $argsList += @("--evidence", $item) }
if ($证据文件 -ne "") { $argsList += @("--evidence-file", $证据文件) }
if ($输出文件 -ne "") { $argsList += @("--output", $输出文件) }

python $pythonScript @argsList
