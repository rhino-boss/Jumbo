@echo off
setlocal
cd /d "%~dp0"
py -3 xlsx_to_config.py --all
if errorlevel 1 exit /b %errorlevel%
echo H013 config_92.js and config_94.js updated.
