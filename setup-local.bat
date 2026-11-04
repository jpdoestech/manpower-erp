@echo off
setlocal DisableDelayedExpansion
title Manpower ERP - SQLite setup
pushd "%~dp0"
if errorlevel 1 exit /b 1
set "ERP_LOCAL_UV="
if exist ".tools\Scripts\uv.exe" set "ERP_LOCAL_UV=%CD%\.tools\Scripts\uv.exe"
if not defined ERP_LOCAL_UV for /f "delims=" %%I in ('where uv.exe 2^>nul') do if not defined ERP_LOCAL_UV set "ERP_LOCAL_UV=%%I"
if not defined ERP_LOCAL_UV (
    echo ERROR: Install uv 0.13.7 and Node.js 24, then reopen setup-local.bat.
    echo See docs\LOCAL_WINDOWS_SETUP.md for prerequisite commands.
    goto failed
)
"%ERP_LOCAL_UV%" --version | findstr /r /c:"^uv 0\.13\.7$" /c:"^uv 0\.13\.7 " >nul
if errorlevel 1 (
    echo ERROR: uv 0.13.7 is required. See docs\LOCAL_WINDOWS_SETUP.md.
    goto failed
)
where node.exe >nul 2>&1
if errorlevel 1 (
    echo ERROR: Install Node.js 24 and reopen this script.
    goto failed
)
set "UV_PYTHON_INSTALL_DIR=%CD%\.tools\python"
set "UV_PROJECT_ENVIRONMENT=%CD%\backend\.venv"
set "UV_PYTHON=3.13.18"
set "PYTHONPATH="
"%ERP_LOCAL_UV%" python install 3.13.18 --no-bin --no-registry
if errorlevel 1 goto failed
pushd backend
"%ERP_LOCAL_UV%" sync --locked --managed-python
if errorlevel 1 (
    popd
    goto failed
)
popd
set "ERP_SETUP_ARGUMENT="
if /I "%~1"=="--no-account" set "ERP_SETUP_ARGUMENT=--no-account"
"backend\.venv\Scripts\python.exe" scripts\windows\local.py setup %ERP_SETUP_ARGUMENT%
if errorlevel 1 goto failed
echo Setup complete. Double-click start-local.bat to run the system.
popd
pause
exit /b 0

:failed
echo Setup failed. Existing configuration and database files have been retained.
popd
pause
exit /b 1
