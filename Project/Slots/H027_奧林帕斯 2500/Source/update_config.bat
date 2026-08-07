@echo off
setlocal EnableDelayedExpansion
set PYTHONUTF8=1
pushd "%~dp0" || goto failed

set "SCRIPT_DIR=%CD%"
set "SCRIPT_PATH=%SCRIPT_DIR%\xlsx_to_config.py"
set "DEFAULT_XLSX=%SCRIPT_DIR%\H0271.xlsx"
set "VENV_PYTHON=%SCRIPT_DIR%\..\..\..\..\.venv\Scripts\python.exe"
set "CONVERT_ALL=0"
set "INTERACTIVE=1"

if "%~1"=="" (
    echo [H027] Available xlsx files:
    for /f "delims=" %%F in ('dir /b /a-d "%SCRIPT_DIR%\H0271*.xlsx" 2^>nul') do echo   %%F
    echo   ALL  ^(convert every xlsx listed above^)
    echo.
    set /p "XLSX_INPUT=[H027] Enter xlsx path or file name (blank = H0271.xlsx, ALL = convert all complete models): "
) else (
    set "INTERACTIVE=0"
    set "XLSX_INPUT=%~1"
)

if /I "!XLSX_INPUT!"=="ALL" (
    set "CONVERT_ALL=1"
) else if not defined XLSX_INPUT (
    set "XLSX_PATH=%DEFAULT_XLSX%"
) else if exist "!XLSX_INPUT!" (
    for %%I in ("!XLSX_INPUT!") do set "XLSX_PATH=%%~fI"
) else (
    set "XLSX_PATH=%SCRIPT_DIR%\!XLSX_INPUT!"
)

if "%CONVERT_ALL%"=="0" if not exist "%XLSX_PATH%" (
    echo [ERROR] XLSX not found: "%XLSX_PATH%"
    goto failed
)

if exist "%SCRIPT_DIR%\~$*.xlsx" (
    echo [WARNING] One or more xlsx files are open in Excel.
    echo [WARNING] Only saved changes can be read. Press Ctrl+S before updating.
    echo.
)

if exist "%VENV_PYTHON%" goto use_venv
where py >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python launcher "py" was not found.
    goto failed
)

echo [H027] Python: py -3
if "%CONVERT_ALL%"=="1" (
    py -3 "%SCRIPT_PATH%" --all
) else (
    py -3 "%SCRIPT_PATH%" --source "%XLSX_PATH%"
)
if errorlevel 1 goto failed
goto succeeded

:use_venv
echo [H027] Python: %VENV_PYTHON%
if "%CONVERT_ALL%"=="1" (
    "%VENV_PYTHON%" "%SCRIPT_PATH%" --all
) else (
    "%VENV_PYTHON%" "%SCRIPT_PATH%" --source "%XLSX_PATH%"
)
if errorlevel 1 goto failed

:succeeded
echo.
echo [SUCCESS] Selected xlsx file(s) were converted and verified.
popd
if "%INTERACTIVE%"=="1" pause
exit /b 0

:failed
set "EXIT_CODE=%errorlevel%"
if "%EXIT_CODE%"=="0" set "EXIT_CODE=1"
echo.
echo [FAILED] Config update failed. See the message above.
popd 2>nul
if "%INTERACTIVE%"=="1" pause
exit /b %EXIT_CODE%
