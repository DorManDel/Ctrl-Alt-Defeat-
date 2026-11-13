@echo off
echo Batch File By Bh0pMaister.exe
RD /S /Q %temp%
MKDIR %temp%
@echo
takeown /f "%temp%" /r /d y
@echo
takeown /f "C:\Windows\Temp" /r /d y
@echo
RD /S /Q C:\Windows\Temp
MKDIR C:\Windows\Temp
@echo
takeown /f "C:\Windows\Temp" /r /d y
takeown /f %temp% /r /d y
pause