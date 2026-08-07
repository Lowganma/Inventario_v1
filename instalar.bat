@echo off
setlocal
cd /d "%~dp0"

where docker >nul 2>nul
if errorlevel 1 (
    echo ERROR: Primero instala Docker Desktop y vuelve a ejecutar este archivo.
    pause
    exit /b 1
)

if not exist .env (
    copy /Y .env.example .env >nul
    for /f %%i in ('powershell -NoProfile -Command "[guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N')"') do set "SECRET=%%i"
    powershell -NoProfile -Command "(Get-Content '.env') -replace 'cambia-esto-por-una-clave-larga-y-unica', $env:SECRET | Set-Content '.env'"
)

echo Instalando Inventario v1. La primera vez puede tardar varios minutos...
docker compose up -d --build
if errorlevel 1 (
    echo ERROR: Docker no pudo iniciar la aplicacion. Revisa que Docker Desktop este abierto.
    pause
    exit /b 1
)

echo.
echo Instalacion terminada. Abriendo la pagina de registro...
start "" http://localhost:8000/usuarios/registro/
pause
