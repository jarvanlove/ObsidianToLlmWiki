param(
    [int]$过期天数 = 45
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
python (Join-Path $scriptDir 'lint_wiki.py') --stale-days $过期天数
