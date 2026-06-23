$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

$pyInstaller = Join-Path $PSScriptRoot ".venv\Scripts\pyinstaller.exe"
if (-not (Test-Path $pyInstaller)) {
    throw "PyInstaller was not found at $pyInstaller"
}

& $pyInstaller --clean --noconfirm ".\IFCBatchConverterDemo.spec"

$iscc = (Get-Command "ISCC.exe" -ErrorAction SilentlyContinue).Source
if (-not $iscc) {
    $candidates = @(
        "${env:LOCALAPPDATA}\Programs\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles}\Inno Setup 6\ISCC.exe"
    )

    $iscc = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
}

if (-not $iscc) {
    throw "Inno Setup compiler was not found. Install Inno Setup 6, then run this script again."
}

& $iscc ".\IFCBatchConverterDemo.iss"

Write-Host ""
Write-Host "Installer created: installer_output\IFCBatchConverterDemo_Setup.exe"
