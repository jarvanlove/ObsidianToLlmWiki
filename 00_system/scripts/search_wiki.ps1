param(
    [Parameter(Mandatory = $true)]
    [string]$关键词,

    [int]$数量 = 10,
    [string]$项目 = "",
    [string]$类型 = "",
    [string]$标签 = ""
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
python (Join-Path $scriptDir 'search_wiki.py') $关键词 --limit $数量 --project $项目 --type $类型 --tag $标签
