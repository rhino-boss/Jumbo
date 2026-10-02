@echo off
setlocal

set "SOURCE_DIR=%~dp0"
set "SCRIPT_PATH=%SOURCE_DIR%xlsx_to_config.py"

echo [H025] Generating 92A / 92B / 94A / 94B config files...
py -3 "%SCRIPT_PATH%" --all --check

if errorlevel 1 (
  echo.
  echo [H025] Config generation failed.
  pause
  exit /b 1
)

echo.
echo [H025] Config files updated successfully.
pause
