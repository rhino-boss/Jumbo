@echo off
setlocal

set "PROJECT_DIR=%~dp0"
set "SCRIPT_PATH=%PROJECT_DIR%Tool\xlsx_to_config.py"
set "XLSX_PATH=%PROJECT_DIR%Source\H026192.xlsx"
set "OUTPUT_PATH=%PROJECT_DIR%config.js"

echo [H026] Updating config.js from H026192.xlsx...
py "%SCRIPT_PATH%" --xlsx "%XLSX_PATH%" --output "%OUTPUT_PATH%" --template "%OUTPUT_PATH%"

if errorlevel 1 (
  echo.
  echo [H026] Update failed.
  pause
  exit /b 1
)

echo.
echo [H026] config.js updated successfully.
pause
