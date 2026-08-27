@echo off
setlocal
cd /d "%~dp0\.."
"..\..\..\.venv\Scripts\python.exe" "Source\model_sync.py" export --source "Source\H0271.xlsx" --output "config.js"
if errorlevel 1 exit /b %errorlevel%
echo H0271.xlsx to config.js completed and verified.
