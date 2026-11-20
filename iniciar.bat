@echo off
setlocal
cd /d "%~dp0"
title organiza-te
docker compose up -d --wait --wait-timeout 120
if errorlevel 1 (
    echo Comprueba que Docker Desktop este activo y que exista el archivo .env.
    docker compose logs --tail=30 web
    pause
    exit /b 1
)
for /f "delims=" %%P in ('powershell -NoProfile -Command "(docker compose port web 8000).Split(':')[-1]"') do set "puerto=%%P"
if not defined puerto exit /b 1
set "ruta=/"
if /i "%~1"=="registro" set "ruta=/usuarios/registro/"
start "" "http://localhost:%puerto%%ruta%"
exit /b 0
