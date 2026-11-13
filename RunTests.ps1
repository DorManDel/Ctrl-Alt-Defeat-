# Safe local pre-push checks. No UAC, no cleanup, no system modification.
$ErrorActionPreference='Stop'
Set-Location -LiteralPath $PSScriptRoot
Write-Host "CTRL+ALT+DEFEAT  /  PRE-PUSH TESTS" -ForegroundColor Magenta
$exe='python'; $prefix=@()
if (Get-Command py -ErrorAction SilentlyContinue) { $exe='py'; $prefix=@('-3') }
try {
    & $exe @prefix -m compileall -q ctrl_alt_defeat
    if ($LASTEXITCODE -ne 0) { throw 'Compilation failed' }
    & $exe @prefix -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw 'Unit tests failed' }
    Write-Host '[PASS] Source compiles and automated tests pass.' -ForegroundColor Green
    Write-Host 'NEXT: Check docs/WINDOWS_SMOKE_TEST.md before opening a PR.' -ForegroundColor Cyan
} catch {
    Write-Host "[FAIL] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host 'DO NOT PUSH until the failing checks are fixed.' -ForegroundColor Yellow
    Read-Host 'Press Enter to close'
    exit 1
}
Read-Host 'Press Enter to close'
