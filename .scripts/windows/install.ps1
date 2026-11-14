<#
.SYNOPSIS
    Interactive TUI and automated installer for PLUS-ULTRA on Windows 11.
#>
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ForwardArgs
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ScriptsRoot = Split-Path -Parent $ScriptDir
$ProjectRoot = Split-Path -Parent $ScriptsRoot

Set-Location $ProjectRoot

if (Get-Command uv -ErrorAction SilentlyContinue) {
    & uv run python "$ScriptsRoot\install.py" @ForwardArgs
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    & python "$ScriptsRoot\install.py" @ForwardArgs
} else {
    Write-Error "Neither uv nor python was found in PATH."
    exit 1
}

