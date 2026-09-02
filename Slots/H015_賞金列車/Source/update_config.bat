@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "SOURCE_DIR=%~dp0"
set "SCRIPT_PATH=%SOURCE_DIR%xlsx_to_config.py"

if not exist "%SCRIPT_PATH%" (
  echo [H015] Converter not found: "%SCRIPT_PATH%"
  pause
  exit /b 1
)

if not "%~1"=="" (
  if /i "%~1"=="all" goto generate_all
  call :generate_one "%~1"
  if errorlevel 1 goto failed
  goto success_one
)

echo [H015] Available xlsx files:
for %%F in ("%SOURCE_DIR%H0151*.xlsx") do echo   %%~nxF
echo.
set /p "XLSX_INPUT=[H015] Enter xlsx path or file name (blank = generate all): "

if not defined XLSX_INPUT goto generate_all
if /i "%XLSX_INPUT%"=="all" goto generate_all

call :generate_one "%XLSX_INPUT%"
if errorlevel 1 goto failed

:success_one
echo.
echo [H015] Config updated successfully.
pause
exit /b 0

:generate_all
py -3 "%SCRIPT_PATH%" --all
if errorlevel 1 goto failed
echo.
echo [H015] All config files updated successfully.
pause
exit /b 0

:generate_one
set "XLSX_PATH=%~1"
if not exist "!XLSX_PATH!" set "XLSX_PATH=%SOURCE_DIR%!XLSX_PATH!"
if not exist "!XLSX_PATH!" (
  echo [H015] XLSX not found: "!XLSX_PATH!"
  exit /b 1
)
py -3 "%SCRIPT_PATH%" --xlsx "!XLSX_PATH!"
exit /b !errorlevel!

:failed
echo.
echo [H015] Update failed.
pause
exit /b 1
