@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "SOURCE_DIR=%~dp0"
for %%I in ("%SOURCE_DIR%..") do set "PROJECT_DIR=%%~fI"
set "SCRIPT_PATH=%SOURCE_DIR%xlsx_to_config.py"

if not exist "%SCRIPT_PATH%" (
  echo [H026] Converter not found: "%SCRIPT_PATH%"
  pause
  exit /b 1
)

if not "%~1"=="" (
  if /i "%~1"=="all" goto generate_all
  call :resolve_and_generate "%~1"
  if errorlevel 1 goto failed
  goto success_one
)

echo [H026] Available xlsx files:
for %%F in ("%SOURCE_DIR%H0261*.xlsx") do echo   %%~nxF
echo.
set /p "XLSX_INPUT=[H026] Enter xlsx path or file name (blank = generate all): "

if not defined XLSX_INPUT goto generate_all
if /i "%XLSX_INPUT%"=="all" goto generate_all

call :resolve_and_generate "%XLSX_INPUT%"
if errorlevel 1 goto failed

:success_one
echo.
echo [H026] Config updated successfully.
pause
exit /b 0

:generate_all
set "GENERATED_COUNT=0"
for %%F in ("%SOURCE_DIR%H0261*.xlsx") do (
  call :generate_one "%%~fF"
  if errorlevel 1 goto failed
  set /a GENERATED_COUNT+=1
)

if "!GENERATED_COUNT!"=="0" (
  echo [H026] No H0261*.xlsx files found in "%SOURCE_DIR%".
  goto failed
)

echo.
echo [H026] !GENERATED_COUNT! config files updated successfully.
pause
exit /b 0

:resolve_and_generate
set "INPUT_PATH=%~1"
if exist "!INPUT_PATH!" (
  for %%I in ("!INPUT_PATH!") do set "RESOLVED_XLSX=%%~fI"
) else (
  set "RESOLVED_XLSX=%SOURCE_DIR%!INPUT_PATH!"
)

if not exist "!RESOLVED_XLSX!" (
  echo [H026] XLSX not found: "!RESOLVED_XLSX!"
  exit /b 1
)

call :generate_one "!RESOLVED_XLSX!"
exit /b !errorlevel!

:generate_one
set "XLSX_PATH=%~f1"
for %%I in ("!XLSX_PATH!") do set "XLSX_NAME=%%~nI"

if /i not "!XLSX_NAME:~0,5!"=="H0261" (
  echo [H026] Unsupported xlsx name: "!XLSX_NAME!"
  echo [H026] Expected format: H026192A.xlsx
  exit /b 1
)

set "CONFIG_SUFFIX=!XLSX_NAME:~5!"
if not defined CONFIG_SUFFIX (
  echo [H026] Cannot determine config suffix from "!XLSX_NAME!".
  exit /b 1
)

set "OUTPUT_PATH=%PROJECT_DIR%\config_!CONFIG_SUFFIX!.js"
set "TEMPLATE_PATH=!OUTPUT_PATH!"

echo.
echo [H026] XLSX   : "!XLSX_PATH!"
echo [H026] Output : "!OUTPUT_PATH!"
py -3 "%SCRIPT_PATH%" --xlsx "!XLSX_PATH!" --output "!OUTPUT_PATH!" --template "!TEMPLATE_PATH!"
if errorlevel 1 exit /b 1

exit /b 0

:failed
echo.
echo [H026] Update failed.
pause
exit /b 1
