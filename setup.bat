@echo off
setlocal DisableDelayedExpansion
title Manpower ERP - Local setup
pushd "%~dp0"
if errorlevel 1 exit /b 1

echo Manpower ERP - local development setup
if exist ".env" goto start_stack

echo Creating .env with a random local database password. Credentials will not be displayed.
powershell.exe -NoLogo -NoProfile -NonInteractive -Command "$ErrorActionPreference='Stop'; $rng=[Security.Cryptography.RandomNumberGenerator]::Create(); $bytes=New-Object byte[] 32; $rng.GetBytes($bytes); $rng.Dispose(); $localPassword=-join($bytes | ForEach-Object { $_.ToString('x2') }); $text=[IO.File]::ReadAllText('.env.example').Replace('POSTGRES_PASSWORD=', 'POSTGRES_PASSWORD='+$localPassword).Replace('SET_LOCAL_PASSWORD', $localPassword); $stream=[IO.File]::Open('.env', [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None); try { $raw=[Text.Encoding]::UTF8.GetBytes($text); $stream.Write($raw, 0, $raw.Length) } finally { $stream.Dispose() }" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Could not create .env. Check .env.example, write access and Windows PowerShell.
    goto failed
)

:start_stack
echo Existing .env files are preserved. No database volume will be deleted.
call run.bat --setup
if errorlevel 1 goto failed

choice /C YN /N /M "Create an ordinary local test account? [Y/N] "
if errorlevel 3 goto failed
if errorlevel 2 goto done
call docker --context default compose -f compose.yaml --env-file .env -p manpower-erp exec api .venv/bin/python -c "import sys; from app.identity.cli import main; sys.argv=['identity','create-user',input('Username: ')]; main()"
if errorlevel 1 (
    echo ERROR: Account creation failed. Existing accounts were not reset.
    goto failed
)

:done
echo Setup complete. Double-click run.bat to open the system.
echo Test accounts receive no administrator or company permissions.
popd
pause
exit /b 0

:failed
echo Setup did not complete. Fix the error above and rerun setup.bat.
popd
pause
exit /b 1
