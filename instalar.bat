@echo off
setlocal
cd /d "%~dp0"
title Instalador de organiza-te
docker info >nul 2>nul
if errorlevel 1 (
    echo Instala y abre Docker Desktop antes de continuar.
    goto :error
)
if exist ".env" goto :construir

powershell -NoProfile -Command ^
    "$ErrorActionPreference='Stop'; $bytes=New-Object byte[] 48;" ^
    "$rng=[Security.Cryptography.RandomNumberGenerator]::Create(); try { $rng.GetBytes($bytes) } finally { $rng.Dispose() };" ^
    "$key=[BitConverter]::ToString($bytes).Replace('-',''); $template=[IO.File]::ReadAllText('.env.example');" ^
    "$tmp='.env.'+[guid]::NewGuid(); try { [IO.File]::WriteAllText($tmp,$template.Replace('DJANGO_SECRET_KEY=','DJANGO_SECRET_KEY='+$key)); [IO.File]::Move($tmp,'.env') } finally { if ([IO.File]::Exists($tmp)) { [IO.File]::Delete($tmp) } }"
if errorlevel 1 goto :error

:construir
docker compose build
if errorlevel 1 goto :error
call iniciar.bat registro
exit /b %errorlevel%

:error
echo No se completo la instalacion de organiza-te.
pause
exit /b 1
