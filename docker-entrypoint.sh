#!/bin/sh

set -e

echo "========================================"
echo " Iniciando Control de cuentas"
echo "========================================"


# ------------------------------------------------------------
# Asegura que exista la carpeta de datos persistentes.
# ------------------------------------------------------------

mkdir -p /app/data


# ------------------------------------------------------------
# Aplica migraciones pendientes.
# ------------------------------------------------------------

echo ""
echo "Aplicando migraciones..."

python manage.py migrate --noinput


# ------------------------------------------------------------
# Prepara archivos estáticos para WhiteNoise.
# ------------------------------------------------------------

echo ""
echo "Preparando archivos estaticos..."

python manage.py collectstatic --noinput


# ------------------------------------------------------------
# Actualiza la tasa USD/BCV.
#
# IMPORTANTE:
# Si la API externa falla, NO detenemos la aplicación.
# Django seguirá funcionando con la última tasa almacenada.
# ------------------------------------------------------------

echo ""
echo "Consultando tasa BCV..."

python manage.py actualizar_tasa_bcv \
    || echo "No fue posible actualizar la tasa BCV. Se utilizara la ultima tasa disponible."


# ------------------------------------------------------------
# Inicia Gunicorn utilizando el CMD del Dockerfile.
# ------------------------------------------------------------

echo ""
echo "Iniciando servidor..."

exec "$@"