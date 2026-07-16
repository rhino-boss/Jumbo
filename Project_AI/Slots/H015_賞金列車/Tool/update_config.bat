@echo off
setlocal

set "TOOL_DIR=%~dp0"
set "PROJECT_DIR=%TOOL_DIR%.."
set "SCRIPT_PATH=%TOOL_DIR%xlsx_to_config.py"
set "OUTPUT_PATH=%PROJECT_DIR%\config.js"
set "TEMPLATE_PATH=%OUTPUT_PATH%"

if "%~1"=="" (
  set "XLSX_PATH=%PROJECT_DIR%\Source\H015192.xlsx"
) else (
  set "XLSX_PATH=%~1"
)

echo [H015] Updating config.js...
echo [H015] XLSX    : "%XLSX_PATH%"
echo [H015] Output  : "%OUTPUT_PATH%"
echo [H015] Template: "%TEMPLATE_PATH%"
py -3 "%SCRIPT_PATH%" --xlsx "%XLSX_PATH%" --output "%OUTPUT_PATH%" --template "%TEMPLATE_PATH%"

if errorlevel 1 (
  echo.
  echo [H015] Update failed.
  pause
  exit /b 1
)

echo.
echo [H015] config.js updated successfully.
pause
