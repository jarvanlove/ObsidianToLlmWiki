param(
    [string]$Task = ""
)

$context = Get-Content "wiki.context.json" -Raw | ConvertFrom-Json
$scaffoldRoot = $context.runtime_root
if ([string]::IsNullOrWhiteSpace($scaffoldRoot)) {
    $scaffoldRoot = $env:OBSIDIANTOWIKI_SCAFFOLD_ROOT
}
if ([string]::IsNullOrWhiteSpace($scaffoldRoot)) {
    Write-Error "wiki.context.json does not contain runtime_root; update the ObsidianToWiki project bridge."
    exit 1
}

$scriptPath = Join-Path $scaffoldRoot "00_system\scripts\project_session.py"
$python = Join-Path $scaffoldRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { $python = "python" }
& $python $scriptPath start --repo-root . --task $Task
