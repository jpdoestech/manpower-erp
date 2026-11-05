@echo off
setlocal DisableDelayedExpansion
title Manpower ERP - SQLite local development
pushd "%~dp0"
if errorlevel 1 exit /b 1
if not exist "backend\.venv\Scripts\python.exe" (
    echo ERROR: Run setup-local.bat first.
    goto failed
)
set "PYTHONPATH="
set "ERP_START_ARGUMENT="
if /I "%~1"=="--no-browser" set "ERP_START_ARGUMENT=--no-browser"
"backend\.venv\Scripts\python.exe" scripts\windows\local.py start %ERP_START_ARGUMENT%
if errorlevel 1 goto failed
popd
exit /b 0

:failed
echo Startup failed. See .local\logs for server diagnostics.
popd
pause
exit /b 1
