param(
    [Parameter(Mandatory = $true)]
    [string]$标题,

    [Parameter(Mandatory = $true)]
    [string]$类型,

    [string]$项目 = "",
    [string]$标签 = "",
    [string]$状态 = "活跃",
    [string]$摘要 = ""
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
python (Join-Path $scriptDir 'create_page.py') --title $标题 --type $类型 --project $项目 --tags $标签 --status $状态 --summary $摘要
