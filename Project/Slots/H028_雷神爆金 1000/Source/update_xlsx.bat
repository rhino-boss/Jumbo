@echo off
setlocal EnableExtensions EnableDelayedExpansion
set PYTHONUTF8=1
pushd "%~dp0" || goto failed

set "SCRIPT_DIR=%CD%"
set "PROJECT_DIR=%SCRIPT_DIR%\.."
set "SCRIPT_PATH=%SCRIPT_DIR%\config_to_xlsx.py"
set "DEFAULT_CONFIG=%PROJECT_DIR%\config_92A.js"
set "DEFAULT_XLSX=%SCRIPT_DIR%\H028192A.xlsx"
set "VENV_PYTHON=%SCRIPT_DIR%\..\..\..\..\.venv\Scripts\python.exe"

if not exist "%SCRIPT_PATH%" (
    echo [ERROR] Tool not found: "%SCRIPT_PATH%"
    goto failed
)

if "%~1"=="" (
    echo [H028] Available config files:
    for /f "delims=" %%F in ('dir /b /a-d "%PROJECT_DIR%\config_*.js" 2^>nul') do echo   %%F
    echo.
    set /p "CONFIG_INPUT=[H028] Enter config path or file name (blank = config_92A.js): "
) else (
    set "CONFIG_INPUT=%~1"
)

if not defined CONFIG_INPUT (
    set "CONFIG_PATH=%DEFAULT_CONFIG%"
) else if exist "!CONFIG_INPUT!" (
    for %%I in ("!CONFIG_INPUT!") do set "CONFIG_PATH=%%~fI"
) else (
    set "CONFIG_PATH=%PROJECT_DIR%\!CONFIG_INPUT!"
)

if not exist "!CONFIG_PATH!" (
    echo.
    echo [ERROR] Config not found: "!CONFIG_PATH!"
    goto failed
)

if "%~2"=="" (
    echo.
    echo [H028] Available source xlsx files:
    for /f "delims=" %%F in ('dir /b /a-d "%SCRIPT_DIR%\H0281*.xlsx" 2^>nul') do echo   %%F
    echo.
    set /p "XLSX_INPUT=[H028] Enter xlsx path or file name (blank = H028192A.xlsx): "
) else (
    set "XLSX_INPUT=%~2"
)

if not defined XLSX_INPUT (
    set "XLSX_PATH=%DEFAULT_XLSX%"
) else if exist "!XLSX_INPUT!" (
    for %%I in ("!XLSX_INPUT!") do set "XLSX_PATH=%%~fI"
) else (
    set "XLSX_PATH=%SCRIPT_DIR%\!XLSX_INPUT!"
)

if not exist "!XLSX_PATH!" (
    echo.
    echo [ERROR] XLSX not found: "!XLSX_PATH!"
    goto failed
)

if exist "%SCRIPT_DIR%\~$*.xlsx" (
    echo.
    echo [WARNING] One or more xlsx files are open in Excel.
    echo [WARNING] Close Excel before overwriting the selected workbook.
)

echo.
echo [H028] Config: "!CONFIG_PATH!"
echo [H028] XLSX: "!XLSX_PATH!"
echo [H028] Mode: overwrite the selected xlsx in place
echo [WARNING] The selected xlsx will be replaced. No separate copy will be created.

if exist "%VENV_PYTHON%" goto use_venv

where py >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python launcher "py" was not found.
    goto failed
)
echo [H028] Python: py -3
py -3 "%SCRIPT_PATH%" --config "!CONFIG_PATH!" --source "!XLSX_PATH!" --in-place --overwrite-formulas
if errorlevel 1 goto failed
goto succeeded

:use_venv
echo [H028] Python: %VENV_PYTHON%
"%VENV_PYTHON%" "%SCRIPT_PATH%" --config "!CONFIG_PATH!" --source "!XLSX_PATH!" --in-place --overwrite-formulas
if errorlevel 1 goto failed

:succeeded
echo.
echo [SUCCESS] Selected xlsx was overwritten and round-trip verified.
popd
pause
exit /b 0

:failed
set "EXIT_CODE=%errorlevel%"
if "%EXIT_CODE%"=="0" set "EXIT_CODE=1"
echo.
echo [FAILED] Xlsx update failed. See the message above.
popd 2>nul
pause
exit /b %EXIT_CODE%
