@echo off
setlocal EnableDelayedExpansion
set PYTHONUTF8=1
pushd "%~dp0" || goto failed
set "SCRIPT_DIR=%CD%"
set "BASE_XLSX=%SCRIPT_DIR%\H0281.xlsx"

rem ---- pick an interpreter -------------------------------------------------
rem Keep the exe and its switches apart: the repo path contains a space, so the
rem exe must always be invoked quoted, and "py -3" cannot be quoted as one token.
set "VENV_PYTHON=%SCRIPT_DIR%\..\..\..\..\.venv\Scripts\python.exe"
if exist "%VENV_PYTHON%" (
    set "PY_EXE=%VENV_PYTHON%"
    set "PY_ARGS="
) else (
    where py >nul 2>nul || (echo [ERROR] Python launcher "py" not found. & goto failed)
    set "PY_EXE=py"
    set "PY_ARGS=-3"
)

rem ---- warn if Excel still has a workbook open ------------------------------
if exist "%SCRIPT_DIR%\~$*.xlsx" (
    echo [WARNING] An xlsx is still open in Excel. Save and close it first,
    echo [WARNING] otherwise unsaved edits will not be picked up.
    echo.
)

rem ---- mode ----------------------------------------------------------------
set "MODE=%~1"
if not defined MODE (
    echo ============================================================
    echo  H028 model / config sync
    echo ------------------------------------------------------------
    echo   Base workbook : H0281.xlsx      ^(pay table, reels, Parameter^)
    echo   RTP variants  : H0281*.xlsx     ^(version + Multiplier_Weight^)
    echo ------------------------------------------------------------
    echo   [1] config  : xlsx  -^> config_*.js   ^(every RTP variant^)
    echo   [2] xlsx    : config_*.js -^> H0281.xlsx
    echo   [3] check   : verify without writing anything
    echo ============================================================
    set /p "MODE=Select [1/2/3] (blank = 1): "
)
if not defined MODE set "MODE=1"
if "%MODE%"=="1" set "MODE=config"
if "%MODE%"=="2" set "MODE=xlsx"
if "%MODE%"=="3" set "MODE=check"

if /I "%MODE%"=="config" goto do_config
if /I "%MODE%"=="xlsx"   goto do_xlsx
if /I "%MODE%"=="check"  goto do_check
echo [ERROR] Unknown mode: %MODE%   ^(use config ^| xlsx ^| check^)
goto failed

rem ==========================================================================
:do_config
echo.
echo [H028] xlsx -^> config  (all RTP variants, base = H0281.xlsx)
"%PY_EXE%" %PY_ARGS% "%SCRIPT_DIR%\model_sync.py" export --all --sync-default
if errorlevel 1 goto failed
"%PY_EXE%" %PY_ARGS% "%SCRIPT_DIR%\model_sync.py" export --all --sync-default --check
if errorlevel 1 goto failed
goto succeeded

rem ==========================================================================
:do_xlsx
echo.
echo [H028] config -^> xlsx  (writes %BASE_XLSX%)
echo        Shared fields go to H0281.xlsx; version/card weights go to every
echo        matching H0281^<RTP^>^<variant^>.xlsx while formulas are preserved.
if not exist "%BASE_XLSX%" (echo [ERROR] Base workbook missing: "%BASE_XLSX%" & goto failed)
"%PY_EXE%" %PY_ARGS% "%SCRIPT_DIR%\model_sync.py" import --source "%BASE_XLSX%" --in-place --overwrite-formulas --force
if errorlevel 1 goto failed
"%PY_EXE%" %PY_ARGS% "%SCRIPT_DIR%\model_sync.py" import --all-variants
if errorlevel 1 goto failed
echo.
echo [H028] re-exporting configs so both directions agree
"%PY_EXE%" %PY_ARGS% "%SCRIPT_DIR%\model_sync.py" export --all --sync-default
if errorlevel 1 goto failed
goto succeeded

rem ==========================================================================
:do_check
echo.
echo [H028] check only - no files are written
"%PY_EXE%" %PY_ARGS% "%SCRIPT_DIR%\model_sync.py" export --all --sync-default --check
if errorlevel 1 goto failed
goto succeeded

rem ==========================================================================
:succeeded
echo.
echo [SUCCESS] Done.
popd
pause
exit /b 0

:failed
set "EXIT_CODE=%errorlevel%"
if "%EXIT_CODE%"=="0" set "EXIT_CODE=1"
echo.
echo [FAILED] See the message above.
popd 2>nul
pause
exit /b %EXIT_CODE%
