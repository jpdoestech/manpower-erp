@echo off
setlocal DisableDelayedExpansion
title Manpower ERP - Local development
pushd "%~dp0"
if errorlevel 1 exit /b 1

where docker >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker was not found. Install Docker Desktop and reopen this script.
    goto failed
)
call docker --context default compose version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker Compose is unavailable. Enable Compose in Docker Desktop.
    goto failed
)
call docker --context default info --format "{{.OSType}}" 2>nul | findstr /x "linux" >nul
if errorlevel 1 (
    echo ERROR: Start Docker Desktop in Linux-container mode using its local default context.
    goto failed
)
if not exist ".env" (
    echo ERROR: Local configuration is missing. Run setup.bat first.
    goto failed
)
call docker --context default compose -f compose.yaml --env-file .env -p manpower-erp config --quiet >nul 2>&1
if errorlevel 1 (
    echo ERROR: Invalid .env or Compose configuration. Set POSTGRES_PASSWORD and check compose.yaml.
    echo Your existing .env has not been changed. Do not share its contents.
    goto failed
)

echo Building and starting the local database, migrations, API and web app. First build may take several minutes.
call docker --context default compose -f compose.yaml --env-file .env -p manpower-erp up --build --wait --wait-timeout 180
if errorlevel 1 (
    echo ERROR: Startup or readiness failed. Check Docker Desktop and ports 5432, 8000 and 5173.
    echo Existing containers and database volume have been retained for inspection.
    goto failed
)
echo System ready: http://127.0.0.1:5173
echo API documentation: http://127.0.0.1:8000/docs
echo Closing this window does not stop the containers.
if /I "%~1"=="--setup" goto done
start "" "http://127.0.0.1:5173"
pause

:done
popd
exit /b 0

:failed
if /I not "%~1"=="--setup" pause
popd
exit /b 1
