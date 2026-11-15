<#
.SYNOPSIS
    Interactive TUI and automated uninstaller for PLUS-ULTRA on Windows 11.
#>
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ForwardArgs
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Set-Location $ProjectRoot

if (Get-Command uv -ErrorAction SilentlyContinue) {
    & uv run python "$ScriptDir\uninstall.py" @ForwardArgs
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    & python "$ScriptDir\uninstall.py" @ForwardArgs
} else {
    Write-Error "Neither uv nor python was found in PATH."
    exit 1
}

