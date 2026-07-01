@echo off
setlocal EnableDelayedExpansion

set "SOURCE_DIR=%~dp0"
for %%I in ("%SOURCE_DIR%..") do set "PROJECT_DIR=%%~fI"
set "SCRIPT_PATH=%SOURCE_DIR%xlsx_to_config.py"
set "OUTPUT_PATH=%PROJECT_DIR%\config.js"
set "TEMPLATE_PATH=%OUTPUT_PATH%"
set "DEFAULT_XLSX_PATH=%SOURCE_DIR%H026192.xlsx"

if "%~1"=="" (
  echo [H026] Available xlsx files:
  for %%F in ("%SOURCE_DIR%*.xlsx") do echo   %%~nxF
  echo.
  set /p "XLSX_INPUT=[H026] Enter xlsx path or file name (blank = H026192.xlsx): "
  if not defined XLSX_INPUT (
    set "XLSX_PATH=%DEFAULT_XLSX_PATH%"
  ) else (
    if exist "!XLSX_INPUT!" (
      set "XLSX_PATH=!XLSX_INPUT!"
    ) else (
      set "XLSX_PATH=%SOURCE_DIR%!XLSX_INPUT!"
    )
  )
) else (
  set "XLSX_PATH=%~1"
)

if not exist "%XLSX_PATH%" (
  echo.
  echo [H026] XLSX not found: "%XLSX_PATH%"
  pause
  exit /b 1
)

echo [H026] Updating config.js...
echo [H026] XLSX    : "%XLSX_PATH%"
echo [H026] Default : "%DEFAULT_XLSX_PATH%"
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
