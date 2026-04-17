param(
    [Parameter(Mandatory = $true)]
    [string]$请求,

    [string]$仓库根目录 = ".",
    [string]$Wiki根目录 = "",
    [string]$源文件 = "",
    [string]$标题 = "",
    [string]$问题 = "",
    [string]$结论 = "",
    [string]$标签 = ""
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$args = @(
    (Join-Path $scriptDir 'handle_nl_request.py'),
    '--request', $请求,
    '--repo-root', $仓库根目录
)

if ($Wiki根目录) { $args += @('--wiki-root', $Wiki根目录) }
if ($源文件) { $args += @('--source', $源文件) }
if ($标题) { $args += @('--title', $标题) }
if ($问题) { $args += @('--question', $问题) }
if ($结论) { $args += @('--conclusion', $结论) }
if ($标签) { $args += @('--tags', $标签) }

python @args
