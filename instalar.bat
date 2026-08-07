@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM ============================================================
REM INVENTARIO V1 - INSTALADOR PARA WINDOWS
REM ============================================================
REM Este archivo prepara y levanta la aplicacion mediante Docker.
REM El usuario final no necesita instalar Python ni Django.
REM ============================================================

title Instalador - Control de cuentas

REM Siempre trabajar desde la carpeta donde esta este archivo.
cd /d "%~dp0"

cls

echo.
echo ============================================================
echo           CONTROL DE CUENTAS - INSTALACION
echo ============================================================
echo.
echo Este proceso preparara la aplicacion automaticamente.
echo La primera instalacion puede tardar varios minutos.
echo.


REM ============================================================
REM 1. COMPROBAR QUE DOCKER ESTA INSTALADO
REM ============================================================

echo [1/6] Comprobando Docker...

where docker >nul 2>nul

if errorlevel 1 (
    echo.
    echo [ERROR] Docker no esta instalado o Windows no lo encuentra.
    echo.
    echo Instala Docker Desktop y vuelve a ejecutar instalar.bat.
    echo.
    pause
    exit /b 1
)

echo       Docker encontrado.


REM ============================================================
REM 2. COMPROBAR QUE DOCKER DESKTOP ESTA FUNCIONANDO
REM ============================================================

echo.
echo [2/6] Comprobando Docker Desktop...

docker info >nul 2>nul

if errorlevel 1 (
    echo.
    echo [ERROR] Docker esta instalado, pero el motor no esta disponible.
    echo.
    echo Abre Docker Desktop y espera hasta que indique:
    echo "Engine running"
    echo.
    echo Luego vuelve a ejecutar este instalador.
    echo.
    pause
    exit /b 1
)

echo       Docker Desktop esta funcionando.


REM ============================================================
REM 3. COMPROBAR DOCKER COMPOSE
REM ============================================================

echo.
echo [3/6] Comprobando Docker Compose...

docker compose version >nul 2>nul

if errorlevel 1 (
    echo.
    echo [ERROR] Docker Compose no esta disponible.
    echo.
    echo Actualiza Docker Desktop e intenta nuevamente.
    echo.
    pause
    exit /b 1
)

echo       Docker Compose disponible.


REM ============================================================
REM 4. CREAR CONFIGURACION PRIVADA
REM ============================================================

echo.
echo [4/6] Preparando configuracion...

if not exist ".env" (

    if not exist ".env.example" (
        echo.
        echo [ERROR] No se encontro el archivo .env.example.
        echo La instalacion no puede continuar.
        echo.
        pause
        exit /b 1
    )

    copy /Y ".env.example" ".env" >nul

    REM Generar una clave aleatoria suficientemente larga.
    for /f "usebackq delims=" %%i in (`powershell -NoProfile -Command "$a=[guid]::NewGuid().ToString('N'); $b=[guid]::NewGuid().ToString('N'); Write-Output ($a+$b)"`) do (
        set "SECRET_KEY=%%i"
    )

    REM Sustituye el marcador de la clave en .env.
    powershell -NoProfile -Command ^
        "$p='.env';" ^
        "$c=Get-Content $p -Raw;" ^
        "$c=$c -replace 'cambia-esto-por-una-clave-larga-y-unica','%SECRET_KEY%';" ^
        "Set-Content -Path $p -Value $c -Encoding ASCII"

    if errorlevel 1 (
        echo.
        echo [ERROR] No se pudo preparar el archivo .env.
        echo.
        pause
        exit /b 1
    )

    echo       Configuracion privada creada.

) else (

    echo       Ya existe .env.
    echo       Se conservara la configuracion existente.

)


REM ============================================================
REM 5. CONSTRUIR E INICIAR LA APLICACION
REM ============================================================

echo.
echo [5/6] Construyendo e iniciando la aplicacion...
echo.
echo Esto puede tardar varios minutos la primera vez.
echo.

docker compose up -d --build

if errorlevel 1 (
    echo.
    echo ============================================================
    echo [ERROR] Docker no pudo construir o iniciar la aplicacion.
    echo ============================================================
    echo.
    echo Ultimos mensajes:
    echo.
    docker compose logs --tail=50 web
    echo.
    pause
    exit /b 1
)


REM ============================================================
REM 6. ESPERAR A QUE DJANGO ESTE REALMENTE DISPONIBLE
REM ============================================================

echo.
echo [6/6] Esperando a que la aplicacion este lista...

set /a INTENTOS=0
set /a MAX_INTENTOS=30

:esperar_app

set /a INTENTOS+=1

powershell -NoProfile -Command ^
    "try { $r=Invoke-WebRequest -UseBasicParsing -Uri 'http://localhost:8000/' -TimeoutSec 3; if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) { exit 0 } else { exit 1 } } catch { exit 1 }"

if not errorlevel 1 goto app_lista

REM Comprobar también si el contenedor murio o esta reiniciando.
docker compose ps --status running | findstr /I "web" >nul

if errorlevel 1 (
    echo.
    echo ============================================================
    echo [ERROR] La aplicacion no pudo iniciar correctamente.
    echo ============================================================
    echo.
    echo Docker devolvio estos mensajes:
    echo.
    docker compose logs --tail=100 web
    echo.
    echo Copia estos mensajes si necesitas soporte tecnico.
    echo.
    pause
    exit /b 1
)

if !INTENTOS! GEQ !MAX_INTENTOS! (
    echo.
    echo ============================================================
    echo [ERROR] La aplicacion tardo demasiado en responder.
    echo ============================================================
    echo.
    echo Ultimos mensajes de Docker:
    echo.
    docker compose logs --tail=100 web
    echo.
    pause
    exit /b 1
)

echo       Preparando servidor... intento !INTENTOS!/!MAX_INTENTOS!
timeout /t 2 /nobreak >nul

goto esperar_app


REM ============================================================
REM INSTALACION CORRECTA
REM ============================================================

:app_lista

echo.
echo ============================================================
echo             INSTALACION COMPLETADA
echo ============================================================
echo.
echo La aplicacion esta funcionando correctamente.
echo.
echo Direccion:
echo.
echo     http://localhost:8000
echo.
echo Si es tu primera vez, crea tu cuenta en:
echo.
echo     http://localhost:8000/usuarios/registro/
echo.
echo IMPORTANTE:
echo No elimines la carpeta de la aplicacion ni los volumenes
echo de Docker si deseas conservar la informacion.
echo.
echo Abriendo el navegador...
echo.

start "" "http://localhost:8000/usuarios/registro/"

echo.
echo Puedes cerrar esta ventana.
echo.
pause

endlocal
exit /b 0