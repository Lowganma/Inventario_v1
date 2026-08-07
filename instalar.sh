#!/bin/sh
set -eu
cd "$(dirname "$0")"

if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: instala Docker y Docker Compose antes de continuar."
    exit 1
fi

if [ ! -f .env ]; then
    cp .env.example .env
    secret="$(od -An -N48 -tx1 /dev/urandom | tr -d ' \n')"
    sed "s/cambia-esto-por-una-clave-larga-y-unica/$secret/" .env > .env.tmp
    mv .env.tmp .env
fi

echo "Instalando Inventario v1. La primera vez puede tardar varios minutos..."
docker compose up -d --build
echo "Listo: abre http://localhost:8000/usuarios/registro/"
