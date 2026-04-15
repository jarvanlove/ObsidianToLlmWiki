param(
    [Parameter(Mandatory = $true)]
    [string]$项目名,

    [string]$标签 = "",
    [string]$状态 = "活跃",
    [string]$摘要 = ""
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
python (Join-Path $scriptDir 'create_page.py') --title $项目名 --type 项目 --tags $标签 --status $状态 --summary $摘要
