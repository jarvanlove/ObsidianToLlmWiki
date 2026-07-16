param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)

$ErrorActionPreference = "Stop"
python "$PSScriptRoot\doctor.py" @Arguments
