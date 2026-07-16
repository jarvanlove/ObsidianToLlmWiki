param(
    [string]$索引路径 = "",
    [switch]$完全重建
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonArgs = @((Join-Path $scriptDir 'build_retrieval_index.py'))
if ($索引路径) {
    $pythonArgs += @('--index-path', $索引路径)
}
if ($完全重建) {
    $pythonArgs += '--full'
}
python @pythonArgs
