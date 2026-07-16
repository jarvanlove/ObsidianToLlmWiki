param(
    [ValidateSet("report", "migrate")][string]$命令 = "report",
    [switch]$应用,
    [ValidateSet("text", "json")][string]$格式 = "text"
)

$argsList = @($命令, "--format", $格式)
if ($应用) { $argsList += "--apply" }
python "$PSScriptRoot\vault_compat.py" @argsList
