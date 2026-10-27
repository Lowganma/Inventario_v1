@echo off
setlocal
cd /d "%~dp0"
title Inventario - Prueba local
py -3.11 --version >nul 2>nul
if errorlevel 1 goto falta_python
if exist ".venv-prueba\Scripts\python.exe" goto instalar
py -3.11 -m venv .venv-prueba
if errorlevel 1 goto error
:instalar
.venv-prueba\Scripts\python.exe -m pip install -r requirements-prueba.txt
if errorlevel 1 goto error
.venv-prueba\Scripts\python.exe manage.py migrate --noinput
if errorlevel 1 goto error
.venv-prueba\Scripts\python.exe manage.py check
if errorlevel 1 goto error
echo.
echo Abre http://127.0.0.1:8765/usuarios/registro/ para crear tu cuenta.
echo Si ya tienes cuenta, entra en http://127.0.0.1:8765/
echo Deja esta ventana abierta mientras usas el sistema.
echo Para detenerlo, pulsa Ctrl+C.
echo.
start "" "http://127.0.0.1:8765/"
.venv-prueba\Scripts\python.exe manage.py runserver 127.0.0.1:8765 --noreload
if errorlevel 1 goto error
exit /b 0
:falta_python
echo Instala Python 3.11 para Windows y vuelve a abrir este archivo.
echo Marca la opcion de instalar Python Launcher durante la instalacion.
echo Descarga oficial: https://www.python.org/downloads/release/python-3119/
pause
exit /b 1
:error
echo.
echo No se pudo completar el inicio. Conserva el mensaje de error de arriba.
pause
exit /b 1
