@echo off
setlocal
cd /d "%~dp0"
py -3 xlsx_to_config.py
if errorlevel 1 exit /b %errorlevel%
echo H013 config.js updated.
