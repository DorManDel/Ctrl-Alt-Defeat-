# Ctrl+Alt+Defeat v0.5 one-window launcher. Preferred entry: double-click CtrlAltDefeat.vbs.
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$principal = [Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host 'Requesting Administrator permission...' -ForegroundColor Yellow
    try {
        Start-Process -FilePath powershell.exe -Verb RunAs -WorkingDirectory $PSScriptRoot -ArgumentList @(
            '-NoProfile','-ExecutionPolicy','Bypass','-NoExit','-File', ('"' + $PSCommandPath + '"')
        ) | Out-Null
        exit 0
    } catch {
        Write-Host "Administrator approval cancelled: $($_.Exception.Message)" -ForegroundColor Yellow
        exit 1
    }
}
# Prevent silently running the obsolete v0.4 menu from an incomplete extraction.
if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'ctrl_alt_defeat\dashboard.py'))) {
    Write-Host 'ERROR: The new dashboard is missing. Extract the complete v0.5.1 package into a new folder.' -ForegroundColor Red
    Read-Host 'Press Enter to close'
    exit 1
}
$exe = Join-Path $PSScriptRoot 'CtrlAltDefeat.exe'
if (Test-Path -LiteralPath $exe) { & $exe menu; exit $LASTEXITCODE }

$pyCmd = $null
$pyArgs = @()
if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' 2>$null
    if ($LASTEXITCODE -eq 0) { $pyCmd = 'py'; $pyArgs = @('-3') }
}
if (-not $pyCmd -and (Get-Command python -ErrorAction SilentlyContinue)) {
    & python -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' 2>$null
    if ($LASTEXITCODE -eq 0) { $pyCmd = 'python' }
}
if (-not $pyCmd) {
    Write-Host 'Python 3.10+ is needed for source mode. Use the standalone EXE instead when available.' -ForegroundColor Yellow
    $answer = Read-Host 'Install Python 3.12 with winget? [y/N]'
    if ($answer -notin @('y','Y')) { exit 1 }
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Write-Host 'winget not found. Python must be installed manually.' -ForegroundColor Red
        exit 1
    }
    winget install --id Python.Python.3.12 --exact --source winget --accept-source-agreements --accept-package-agreements
    Write-Host 'Close this terminal and launch CtrlAltDefeat.vbs again.'
    exit 0
}
# Standard-library TUI: no pip packages or dynamic dependency installs are required.
& $pyCmd @pyArgs -m ctrl_alt_defeat menu
if ($LASTEXITCODE -ne 0) {
    Write-Host "Ctrl+Alt+Defeat exited with code $LASTEXITCODE" -ForegroundColor Red
    Read-Host 'Press Enter to close'
}
