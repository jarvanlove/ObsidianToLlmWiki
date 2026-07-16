param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)

$ErrorActionPreference = "Stop"
python "$PSScriptRoot\otw.py" @Arguments
