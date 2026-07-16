param(
    [Parameter(Mandatory = $true)]
    [string]$关键词,

    [int]$数量 = 10,
    [string]$项目 = "",
    [string]$类型 = "",
    [string]$标签 = "",
    [ValidateSet("text", "json", "context")]
    [string]$格式 = "text",
    [int]$Token预算 = 4000,
    [switch]$显示关系,
    [switch]$不刷新
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonArgs = @(
    (Join-Path $scriptDir 'search_wiki.py'),
    $关键词,
    '--limit', $数量,
    '--project', $项目,
    '--type', $类型,
    '--tag', $标签,
    '--format', $格式,
    '--token-budget', $Token预算
)
if ($显示关系) {
    $pythonArgs += '--show-relations'
}
if ($不刷新) {
    $pythonArgs += '--no-refresh'
}
python @pythonArgs
