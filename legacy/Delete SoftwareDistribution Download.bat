del %windir%\SoftwareDistribution\Download\. /f /q
for /f "tokens=*" %%i in ('dir %windir%\SoftwareDistribution\Download\. /b') do rd "%windir%\SoftwareDistribution\Download\%%i" /s /q