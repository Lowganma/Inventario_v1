#!/bin/sh
set -eu
cd "$(dirname "$0")"
docker compose version >/dev/null || { echo "Instala Docker con Compose v2 para continuar."; exit 1; }

if [ ! -f .env ]; then
    (
        umask 077
        temporal=$(mktemp .env.XXXXXX)
        trap 'rm -f "$temporal"' EXIT
        clave=$(od -An -N48 -tx1 /dev/urandom | tr -d ' \n')
        {
            printf 'DJANGO_SECRET_KEY=%s\n' "$clave"
            sed '/^DJANGO_SECRET_KEY=/d' .env.example
        } > "$temporal"
        ln "$temporal" .env
    )
fi

docker compose up -d --build --wait --wait-timeout 120
direccion=$(docker compose port web 8000)
echo "Abre http://localhost:${direccion##*:}/usuarios/registro/"
