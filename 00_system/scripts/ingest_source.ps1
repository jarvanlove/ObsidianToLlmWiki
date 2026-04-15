param(
    [Parameter(Mandatory = $true)]
    [string]$源文件,

    [string]$标题 = "",
    [string]$项目 = "",
    [string]$标签 = "",
    [string]$摘要 = ""
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
python (Join-Path $scriptDir 'ingest_source.py') --source $源文件 --title $标题 --project $项目 --tags $标签 --summary $摘要
