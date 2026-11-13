@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if not errorlevel 1 (
  py -3 -m ctrl_alt_defeat.arcade_cli
) else (
  python -m ctrl_alt_defeat.arcade_cli
)
if errorlevel 1 pause
