# Windows launcher. Double-click CtrlAltDefeat.cmd. Runs as administrator after UAC confirmation.
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host 'Ctrl+Alt+Defeat requests Administrator access. Review the Windows UAC prompt.' -ForegroundColor Yellow
    $quoted = '"' + $PSCommandPath.Replace('"', '""') + '"'
    try {
        Start-Process -FilePath 'powershell.exe' -Verb RunAs -WorkingDirectory $PSScriptRoot -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-NoExit','-File', $quoted) | Out-Null
    } catch {
        Write-Host ('Elevation cancelled or failed: ' + $_.Exception.Message) -ForegroundColor Red
        exit 1
    }
    exit 0
}
Write-Host 'CTRL+ALT+DEFEAT // Administrator session' -ForegroundColor Magenta
$py = Get-Command py -ErrorAction SilentlyContinue
$python = Get-Command python -ErrorAction SilentlyContinue
if ($py) {
    & py -3 -m ctrl_alt_defeat menu
} elseif ($python) {
    & python -m ctrl_alt_defeat menu
} else {
    Write-Host 'Python 3.10+ is required by this source-based starter.' -ForegroundColor Yellow
    Write-Host 'Install Python from python.org, then double-click CtrlAltDefeat.cmd again.'
    Write-Host 'A future packaged .exe will not require Python.'
    Read-Host 'Press Enter to close'
    exit 1
}
if ($LASTEXITCODE -ne 0) {
    Write-Host ('Ctrl+Alt+Defeat exited with code ' + $LASTEXITCODE) -ForegroundColor Red
    Read-Host 'Press Enter to close'
    exit $LASTEXITCODE
}
