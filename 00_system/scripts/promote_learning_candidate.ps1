param(
    [Parameter(Mandatory = $true)][string]$来源,
    [Parameter(Mandatory = $true)][string]$目标类型,
    [string]$标题 = ""
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonScript = Join-Path $scriptDir "promote_learning_candidate.py"

$argsList = @("--source", $来源, "--target-type", $目标类型)
if ($标题 -ne "") { $argsList += @("--title", $标题) }

python $pythonScript @argsList
