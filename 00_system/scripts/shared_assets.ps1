param(
    [ValidateSet("report", "stage", "apply-safe")][string]$命令 = "report",
    [string]$私有库根目录 = "",
    [string]$公开库根目录 = "",
    [ValidateSet("text", "json")][string]$格式 = "text"
)

$argsList = @($命令, "--format", $格式)
if ($私有库根目录) { $argsList += @("--vault-root", $私有库根目录) }
if ($公开库根目录) { $argsList += @("--source-root", $公开库根目录) }
python "$PSScriptRoot\shared_assets.py" @argsList
