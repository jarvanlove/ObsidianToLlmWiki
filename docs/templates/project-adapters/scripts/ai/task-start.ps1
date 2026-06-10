param(
    [string]$Task = ""
)

$scaffoldRoot = $env:OBSIDIANTOWIKI_SCAFFOLD_ROOT
if ([string]::IsNullOrWhiteSpace($scaffoldRoot)) {
    Write-Error "Set OBSIDIANTOWIKI_SCAFFOLD_ROOT to your ObsidianToWiki public scaffold root before using this adapter."
    exit 1
}

$scriptPath = Join-Path $scaffoldRoot "00_system\scripts\project_session.py"
python $scriptPath start --repo-root . --task $Task
