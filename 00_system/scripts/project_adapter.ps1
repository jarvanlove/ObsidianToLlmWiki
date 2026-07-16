param(
    [ValidateSet("report", "apply")][string]$命令 = "report",
    [Parameter(Mandatory = $true)][string]$项目根目录,
    [ValidateSet("text", "json")][string]$格式 = "text"
)

python "$PSScriptRoot\project_adapter.py" $命令 --repo-root $项目根目录 --format $格式
