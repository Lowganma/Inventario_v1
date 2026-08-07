@echo off
setlocal

title Control de cuentas

cd /d "%~dp0"

echo.
echo Iniciando Control de cuentas...
echo.

docker info >nul 2>nul

if errorlevel 1 (
    echo Docker Desktop no esta funcionando.
    echo.
    echo Abre Docker Desktop y vuelve a intentarlo.
    echo.
    pause
    exit /b 1
)

docker compose up -d

if errorlevel 1 (
    echo.
    echo No fue posible iniciar la aplicacion.
    echo.
    docker compose logs --tail=50 web
    echo.
    pause
    exit /b 1
)

echo Esperando al servidor...

timeout /t 4 /nobreak >nul

start "" "http://localhost:8000/"

exit /b 0
