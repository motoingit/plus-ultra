<#
.SYNOPSIS
    Installs PLUS-ULTRA for the current user into %LOCALAPPDATA%\Programs\plus-ultra.
.DESCRIPTION
    Creates application directory, copies the compiled standalone executable,
    and registers Start Menu and Desktop shortcuts with the embedded application icon.
#>

param (
    [switch]$BuildIfMissing = $true,
    [switch]$LaunchAfterInstall = $false
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (Get-Item $PSScriptRoot).Parent.FullName
$DistExe = Join-Path $ProjectRoot "dist\plus-ultra.exe"
$InstallDir = Join-Path $env:LOCALAPPDATA "Programs\plus-ultra"
$TargetExe = Join-Path $InstallDir "plus-ultra.exe"
$IconFile = Join-Path $ProjectRoot "src\plus_ultra\resources\icons\app.ico"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  PLUS-ULTRA Desktop Assistant Installer  " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. Build executable if missing
if (-not (Test-Path $DistExe)) {
    if ($BuildIfMissing) {
        Write-Host "Executable not found at dist\plus-ultra.exe. Building via PyInstaller..." -ForegroundColor Yellow
        Push-Location $ProjectRoot
        try {
            uv run pyinstaller plus-ultra.spec --noconfirm
        } finally {
            Pop-Location
        }
    } else {
        Write-Error "dist\plus-ultra.exe does not exist. Run 'uv run pyinstaller plus-ultra.spec' first."
        exit 1
    }
}

# 2. Create Target Directory
Write-Host "Installing to: $InstallDir" -ForegroundColor Green
if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}

# 3. Copy Executable and Icon
Copy-Item -Path $DistExe -Destination $TargetExe -Force
if (Test-Path $IconFile) {
    Copy-Item -Path $IconFile -Destination (Join-Path $InstallDir "app.ico") -Force
}

# 4. Create Desktop & Start Menu Shortcuts using WScript.Shell
$WshShell = New-Object -ComObject WScript.Shell

# Desktop Shortcut
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$DesktopShortcut = Join-Path $DesktopPath "PLUS-ULTRA.lnk"
$Shortcut = $WshShell.CreateShortcut($DesktopShortcut)
$Shortcut.TargetPath = $TargetExe
$Shortcut.WorkingDirectory = $InstallDir
$Shortcut.Description = "PLUS-ULTRA Floating Desktop Assistant"
if (Test-Path (Join-Path $InstallDir "app.ico")) {
    $Shortcut.IconLocation = (Join-Path $InstallDir "app.ico")
}
$Shortcut.Save()
Write-Host "Created Desktop shortcut: $DesktopShortcut" -ForegroundColor Green

# Start Menu Shortcut
$StartMenuPath = [Environment]::GetFolderPath("Programs")
$StartMenuShortcut = Join-Path $StartMenuPath "PLUS-ULTRA.lnk"
$Shortcut = $WshShell.CreateShortcut($StartMenuShortcut)
$Shortcut.TargetPath = $TargetExe
$Shortcut.WorkingDirectory = $InstallDir
$Shortcut.Description = "PLUS-ULTRA Floating Desktop Assistant"
if (Test-Path (Join-Path $InstallDir "app.ico")) {
    $Shortcut.IconLocation = (Join-Path $InstallDir "app.ico")
}
$Shortcut.Save()
Write-Host "Created Start Menu shortcut: $StartMenuShortcut" -ForegroundColor Green

Write-Host "`nInstallation completed successfully!" -ForegroundColor Cyan
Write-Host "Persistent user data is located at:" -ForegroundColor DarkGray
Write-Host "  Database: %LOCALAPPDATA%\plus-ultra\plus-ultra.sqlite3" -ForegroundColor DarkGray
Write-Host "  Settings: %APPDATA%\plus-ultra\user-settings.json" -ForegroundColor DarkGray

if ($LaunchAfterInstall) {
    Write-Host "Launching PLUS-ULTRA..." -ForegroundColor Green
    Start-Process -FilePath $TargetExe
}
