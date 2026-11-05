@echo off
setlocal DisableDelayedExpansion
pushd "%~dp0"
if errorlevel 1 exit /b 1
if not exist "backend\.venv\Scripts\python.exe" (
    echo ERROR: Run setup-local.bat first.
    popd
    pause
    exit /b 1
)
set "PYTHONPATH="
"backend\.venv\Scripts\python.exe" scripts\windows\local.py restore "%~1"
set "ERP_LOCAL_RESULT=%ERRORLEVEL%"
popd
pause
exit /b %ERP_LOCAL_RESULT%
