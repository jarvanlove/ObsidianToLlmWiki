param(
  [Parameter(Mandatory = $true)][string]$Action,
  [string]$RiskLevel = "",
  [string]$UpgradeMode = "",
  [string]$CandidateDomain = "",
  [int]$MinScore,
  [string]$Status = "候选",
  [int]$MaxCount = 0,
  [string]$ReviewNote = "",
  [switch]$Rebuild
)

$script = Join-Path $PSScriptRoot "review_learning_candidates.py"
$argsList = @($script, "--action", $Action, "--status", $Status)

if ($RiskLevel) { $argsList += @("--risk-level", $RiskLevel) }
if ($UpgradeMode) { $argsList += @("--upgrade-mode", $UpgradeMode) }
if ($CandidateDomain) { $argsList += @("--candidate-domain", $CandidateDomain) }
if ($PSBoundParameters.ContainsKey("MinScore")) { $argsList += @("--min-score", "$MinScore") }
if ($MaxCount -gt 0) { $argsList += @("--max-count", "$MaxCount") }
if ($ReviewNote) { $argsList += @("--review-note", $ReviewNote) }
if ($Rebuild) { $argsList += "--rebuild" }

python @argsList
