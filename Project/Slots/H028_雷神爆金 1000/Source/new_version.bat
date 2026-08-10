@echo off
chcp 65001 >nul
setlocal
pushd "%~dp0" || goto failed

set "VENV_PYTHON=%CD%\..\..\..\..\.venv\Scripts\python.exe"
if exist "%VENV_PYTHON%" (
    set "PY_EXE=%VENV_PYTHON%"
    set "PY_ARGS="
) else (
    set "PY_EXE=py"
    set "PY_ARGS=-3"
)

echo.
echo 1. H0281 主要參數（第一碼 +1）
echo 2. 只改倍率權重（第二碼 +1）
echo.
set /p "CHANGE_TYPE=請選擇 [1/2]: "

if "%CHANGE_TYPE%"=="1" (
    "%PY_EXE%" %PY_ARGS% "%CD%\version_history.py" --type main --config all
    if errorlevel 1 goto failed
    goto succeeded
)
if not "%CHANGE_TYPE%"=="2" goto failed

echo.
echo 1. 92A
echo 2. 94A
echo 3. 全部
set /p "TARGET=請選擇 [1/2/3]: "
if "%TARGET%"=="1" set "CONFIG_CODE=92A"
if "%TARGET%"=="2" set "CONFIG_CODE=94A"
if "%TARGET%"=="3" set "CONFIG_CODE=all"
if not defined CONFIG_CODE goto failed

"%PY_EXE%" %PY_ARGS% "%CD%\version_history.py" --type weights --config "%CONFIG_CODE%"
if errorlevel 1 goto failed
goto succeeded

:succeeded
echo.
echo 完成。
popd
pause
exit /b 0

:failed
echo.
echo 版本更新失敗。請確認 XLSX 已關閉，且確實有數學參數差異。
popd
pause
exit /b 1
