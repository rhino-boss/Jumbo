@echo off
setlocal

set "TOOL_DIR=%~dp0"
set "PROJECT_DIR=%TOOL_DIR%.."
set "SCRIPT_PATH=%TOOL_DIR%xlsx_to_config.py"
set "OUTPUT_PATH=%PROJECT_DIR%\config.js"
set "TEMPLATE_PATH=%OUTPUT_PATH%"

if "%~1"=="" (
  set "XLSX_PATH=%PROJECT_DIR%\Source\H026192.xlsx"
) else (
  set "XLSX_PATH=%~1"
)

echo [H026] Updating config.js...
echo [H026] XLSX    : "%XLSX_PATH%"
echo [H026] Output  : "%OUTPUT_PATH%"
echo [H026] Template: "%TEMPLATE_PATH%"
py -3 "%SCRIPT_PATH%" --xlsx "%XLSX_PATH%" --output "%OUTPUT_PATH%" --template "%TEMPLATE_PATH%"

if errorlevel 1 (
  echo.
  echo [H026] Update failed.
  pause
  exit /b 1
)

echo.
echo [H026] config.js updated successfully.
pause
