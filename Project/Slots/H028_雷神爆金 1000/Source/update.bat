@echo off
chcp 65001 >nul
setlocal
pushd "%~dp0" || goto failed

set "SCRIPT_DIR=%CD%"
set "VENV_PYTHON=%SCRIPT_DIR%\..\..\..\..\.venv\Scripts\python.exe"

if exist "%VENV_PYTHON%" (
    set "PY_EXE=%VENV_PYTHON%"
    set "PY_ARGS="
) else (
    where py >nul 2>nul || (
        echo [失敗] 找不到 Python。
        goto failed
    )
    set "PY_EXE=py"
    set "PY_ARGS=-3"
)

echo.
echo 1. XLSX to config
echo 2. config to XLSX
echo.
set /p "DIRECTION=請選擇 [1/2]: "

if "%DIRECTION%"=="1" goto choose_xlsx
if "%DIRECTION%"=="2" goto choose_config
echo [失敗] 請輸入 1 或 2。
goto failed

:choose_xlsx
echo.
echo 1. H0281.xlsx
echo 2. H028192A.xlsx
echo 3. H028194A.xlsx
echo Enter. 全部
echo.
set /p "TARGET=請選擇檔案: "

if not defined TARGET (
    call :xlsx_to_config "H0281.xlsx" "config.js" || goto failed
    call :xlsx_to_config "H028192A.xlsx" "config_92A.js" || goto failed
    call :xlsx_to_config "H028194A.xlsx" "config_94A.js" || goto failed
    goto succeeded
)
if "%TARGET%"=="1" (
    call :xlsx_to_config "H0281.xlsx" "config.js" || goto failed
    goto succeeded
)
if "%TARGET%"=="2" (
    call :xlsx_to_config "H028192A.xlsx" "config_92A.js" || goto failed
    goto succeeded
)
if "%TARGET%"=="3" (
    call :xlsx_to_config "H028194A.xlsx" "config_94A.js" || goto failed
    goto succeeded
)
echo [失敗] 請輸入 1、2、3，或直接按 Enter。
goto failed

:choose_config
echo.
echo 1. config.js
echo 2. config_92A.js
echo 3. config_94A.js
echo Enter. 全部
echo.
set /p "TARGET=請選擇檔案: "

if not defined TARGET (
    call :config_to_xlsx "config.js" "H0281.xlsx" || goto failed
    call :config_to_xlsx "config_92A.js" "H028192A.xlsx" || goto failed
    call :config_to_xlsx "config_94A.js" "H028194A.xlsx" || goto failed
    goto succeeded
)
if "%TARGET%"=="1" (
    call :config_to_xlsx "config.js" "H0281.xlsx" || goto failed
    goto succeeded
)
if "%TARGET%"=="2" (
    call :config_to_xlsx "config_92A.js" "H028192A.xlsx" || goto failed
    goto succeeded
)
if "%TARGET%"=="3" (
    call :config_to_xlsx "config_94A.js" "H028194A.xlsx" || goto failed
    goto succeeded
)
echo [失敗] 請輸入 1、2、3，或直接按 Enter。
goto failed

:xlsx_to_config
if not exist "%SCRIPT_DIR%\%~1" (
    echo [失敗] 找不到 %~1
    exit /b 1
)
echo.
echo [轉換] %~1  -^>  %~2
"%PY_EXE%" %PY_ARGS% "%SCRIPT_DIR%\model_sync.py" export ^
    --source "%SCRIPT_DIR%\%~1" ^
    --output "%SCRIPT_DIR%\..\%~2" >nul
if errorlevel 1 exit /b 1
echo [完成] %~2
exit /b 0

:config_to_xlsx
if not exist "%SCRIPT_DIR%\..\%~1" (
    echo [失敗] 找不到 %~1
    exit /b 1
)
if not exist "%SCRIPT_DIR%\%~2" (
    echo [失敗] 找不到 %~2
    exit /b 1
)
echo.
echo [轉換] %~1  -^>  %~2
"%PY_EXE%" %PY_ARGS% "%SCRIPT_DIR%\model_sync.py" import ^
    --config "%SCRIPT_DIR%\..\%~1" ^
    --source "%SCRIPT_DIR%\%~2" ^
    --in-place ^
    --overwrite-formulas >nul
if errorlevel 1 exit /b 1
echo [完成] %~2
exit /b 0

:succeeded
echo.
echo 全部完成。
popd
pause
exit /b 0

:failed
echo.
echo 轉換失敗。若 XLSX 正在 Excel 中開啟，請先關閉後再試。
popd
pause
exit /b 1
