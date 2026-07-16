param(
    [string]$Output = ""
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
$argsList = @("check", "--repo-root", ".")
if (-not [string]::IsNullOrWhiteSpace($Output)) {
    $argsList += @("--format", "markdown", "--output", $Output)
}

$python = Join-Path $scaffoldRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { $python = "python" }
& $python $scriptPath @argsList
