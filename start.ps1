$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    Write-Host 'Python launcher not found. Install Python 3.11+ first.'
    exit 1
}
py -m ctrl_alt_defeat menu
