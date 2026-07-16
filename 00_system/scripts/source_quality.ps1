param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)

$ErrorActionPreference = "Stop"
python "$PSScriptRoot\source_quality.py" @Arguments
