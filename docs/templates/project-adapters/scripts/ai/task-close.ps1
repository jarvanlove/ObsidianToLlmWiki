param(
    [string]$Verification = "",
    [string]$Output = ""
)

$scaffoldRoot = $env:OBSIDIANTOWIKI_SCAFFOLD_ROOT
if ([string]::IsNullOrWhiteSpace($scaffoldRoot)) {
    Write-Error "Set OBSIDIANTOWIKI_SCAFFOLD_ROOT to your ObsidianToWiki public scaffold root before using this adapter."
    exit 1
}

$scriptPath = Join-Path $scaffoldRoot "00_system\scripts\project_session.py"
$argsList = @("close", "--repo-root", ".", "--verification", $Verification)
if (-not [string]::IsNullOrWhiteSpace($Output)) {
    $argsList += @("--format", "markdown", "--output", $Output)
}

python $scriptPath @argsList
