#!/bin/sh
set -eu

mkdir -p /app/data
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py actualizar_tasa_bcv || echo "Se utilizará la última tasa BCV disponible."
exec "$@"
