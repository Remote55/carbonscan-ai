@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-treeq-demo.ps1" %*
set "TREEQ_EXIT_CODE=%ERRORLEVEL%"
endlocal & exit /b %TREEQ_EXIT_CODE%
