@echo off
set PYTHONUTF8=1
pushd "%~dp0"
set "VENV_PYTHON=%~dp0..\..\..\..\.venv\Scripts\python.exe"
if exist "%VENV_PYTHON%" goto use_venv
py -3 xlsx_to_config.py
if errorlevel 1 exit /b %errorlevel%
py -3 xlsx_to_config.py --check
goto done
:use_venv
"%VENV_PYTHON%" xlsx_to_config.py
if errorlevel 1 exit /b %errorlevel%
"%VENV_PYTHON%" xlsx_to_config.py --check
:done
popd
pause
