param(
    [Parameter(Mandatory = $true)][string]$仓库根目录,
    [Parameter(Mandatory = $true)][string]$项目名,
    [string]$Wiki根目录 = "",
    [string]$标签 = ""
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonScript = Join-Path $scriptDir "attach_project.py"

$argsList = @("--repo-root", $仓库根目录, "--project", $项目名)
if ($Wiki根目录 -ne "") {
    $argsList += @("--wiki-root", $Wiki根目录)
}
if ($标签 -ne "") {
    $argsList += @("--tags", $标签)
}

python $pythonScript @argsList
