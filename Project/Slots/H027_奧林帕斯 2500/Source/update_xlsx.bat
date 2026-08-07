@echo off
setlocal
set PYTHONUTF8=1
pushd "%~dp0" || goto failed

set "SCRIPT_DIR=%CD%"
set "PYTHON=%SCRIPT_DIR%\..\..\..\..\.venv\Scripts\python.exe"
if not exist "%PYTHON%" set "PYTHON=py -3"

echo [H027] Writing config_92A.js back to H0271.xlsx and H027194A.xlsx...
%PYTHON% "%SCRIPT_DIR%\config_to_xlsx.py" --in-place
if errorlevel 1 goto failed

echo.
echo [SUCCESS] Config was written to xlsx and round-trip verified.
popd
pause
exit /b 0

:failed
echo.
echo [FAILED] Config to xlsx failed. See the message above.
popd
pause
exit /b 1
