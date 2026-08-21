@echo off
setlocal
set PYTHONUTF8=1
pushd "%~dp0" || goto failed
set "SCRIPT_DIR=%CD%"
set "MODEL_XLSX=%SCRIPT_DIR%\H0271.xlsx"
set "CONFIG_JS=%SCRIPT_DIR%\..\config.js"

set "VENV_PYTHON=%SCRIPT_DIR%\..\..\..\..\.venv\Scripts\python.exe"
if exist "%VENV_PYTHON%" (
    set "PY_EXE=%VENV_PYTHON%"
    set "PY_ARGS="
) else (
    where py >nul 2>nul || (echo [ERROR] Python launcher "py" not found. & goto failed)
    set "PY_EXE=py"
    set "PY_ARGS=-3"
)

if exist "%SCRIPT_DIR%\~$*.xlsx" (
    echo [WARNING] H0271.xlsx is open in Excel. Save and close it first.
    echo.
)

set "MODE=%~1"
if not defined MODE (
    echo ============================================================
    echo  H027 model / config sync
    echo ------------------------------------------------------------
    echo   [1] config : H0271.xlsx -^> config.js
    echo   [2] xlsx   : config.js -^> H0271.xlsx
    echo   [3] check  : verify base model without writing
    echo   [4] rtp    : H027192A/H027194A -^> config_92A/config_94A
    echo   [5] all    : export and verify base + RTP variants
    echo ============================================================
    set /p "MODE=Select [1/2/3] (blank = 1): "
)
if not defined MODE set "MODE=1"
if "%MODE%"=="1" set "MODE=config"
if "%MODE%"=="2" set "MODE=xlsx"
if "%MODE%"=="3" set "MODE=check"
if "%MODE%"=="4" set "MODE=rtp"
if "%MODE%"=="5" set "MODE=all"

if /I "%MODE%"=="config" goto do_config
if /I "%MODE%"=="xlsx" goto do_xlsx
if /I "%MODE%"=="check" goto do_check
if /I "%MODE%"=="rtp" goto do_rtp
if /I "%MODE%"=="all" goto do_all
echo [ERROR] Unknown mode: %MODE%
goto failed

:do_config
"%PY_EXE%" %PY_ARGS% "%SCRIPT_DIR%\xlsx_to_config.py"
if errorlevel 1 goto failed
"%PY_EXE%" %PY_ARGS% "%SCRIPT_DIR%\xlsx_to_config.py" --check
if errorlevel 1 goto failed
goto succeeded

:do_xlsx
"%PY_EXE%" %PY_ARGS% "%SCRIPT_DIR%\model_sync.py" import --in-place --force
if errorlevel 1 goto failed
"%PY_EXE%" %PY_ARGS% "%SCRIPT_DIR%\xlsx_to_config.py" --check
if errorlevel 1 goto failed
goto succeeded

:do_check
"%PY_EXE%" %PY_ARGS% "%SCRIPT_DIR%\xlsx_to_config.py" --check
if errorlevel 1 goto failed
"%PY_EXE%" %PY_ARGS% "%SCRIPT_DIR%\model_sync.py" import --check
if errorlevel 1 goto failed
goto succeeded

:do_rtp
"%PY_EXE%" %PY_ARGS% "%SCRIPT_DIR%\xlsx_to_config.py" --variants
if errorlevel 1 goto failed
"%PY_EXE%" %PY_ARGS% "%SCRIPT_DIR%\xlsx_to_config.py" --variants --check
if errorlevel 1 goto failed
goto succeeded

:do_all
"%PY_EXE%" %PY_ARGS% "%SCRIPT_DIR%\xlsx_to_config.py" --all
if errorlevel 1 goto failed
"%PY_EXE%" %PY_ARGS% "%SCRIPT_DIR%\xlsx_to_config.py" --all --check
if errorlevel 1 goto failed
goto succeeded

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
