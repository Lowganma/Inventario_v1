# Instalar organiza-te con Docker

Necesitas Docker con Compose v2 que admita `up --wait`. Descarga o clona la rama `rediseno/organiza-te`. Si ya tienes una instalación con datos, sigue primero la [guía de actualización y respaldo](DEMO_HOSTINGER.md#actualizar-una-instalación-con-datos).

## Windows

1. Instala Docker Desktop y espera a que el motor esté en ejecución.
2. Descomprime el proyecto si lo descargaste en ZIP. Abre la carpeta que contiene `compose.yaml`.
3. Haz doble clic en `instalar.bat`. El instalador genera el archivo privado `.env` si hace falta, construye la imagen, espera a que arranque el servicio y abre el registro del negocio.
4. En los siguientes arranques puedes usar `iniciar.bat`.

## Linux

```sh
git clone --branch rediseno/organiza-te https://github.com/Lowganma/Inventario_v1.git
cd Inventario_v1
./instalar.sh
```

Abre <http://localhost:8000/usuarios/registro/> en el equipo donde se está ejecutando Docker.

## Acceso desde la oficina

El puerto se publica inicialmente en `127.0.0.1`. Para compartir la aplicación con teléfonos u otros equipos de la misma red, establece estos valores en `.env` y sustituye la IP de ejemplo por la de tu equipo:

```dotenv
APP_BIND_ADDRESS=0.0.0.0
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.50
```

Aplica el cambio con `docker compose up -d --wait`. Desde el teléfono, abre `http://192.168.1.50:8000/`. Si el firewall de la computadora lo requiere, permite el puerto en la red privada. Para un VPS con el proxy HTTPS en el mismo servidor, conserva el enlace local y sigue la [guía de Hostinger](DEMO_HOSTINGER.md).

## Uso diario y respaldo

| Operación | Comando |
| --- | --- |
| Consultar el estado | `docker compose ps` |
| Leer los últimos mensajes | `docker compose logs --tail=50 web` |
| Detener el servicio | `docker compose stop web` |
| Volver a iniciarlo | `docker compose up -d --wait` |
| Actualizar tras descargar cambios | `docker compose up -d --build --wait` |

Para respaldar, detén el servicio, copia `/app/data/.` del contenedor a una carpeta nueva con `docker compose cp`, copia la carpeta local `media/` y guarda `.env` en un sitio privado. Vuelve a arrancar el servicio. Al restaurar, conserva el nombre de proyecto de Compose, los nombres de las imágenes y la clave de firma. La opción `docker compose down -v` elimina el volumen de SQLite.

Si el puerto está ocupado, cambia `APP_PORT` en `.env`. Si Django muestra `DisallowedHost`, revisa `DJANGO_ALLOWED_HOSTS`. Las credenciales de correo y la clave de firma se configuran en `.env`; `.env.example` contiene los nombres que admite la aplicación.

[Desarrollo local con Pipenv](../README.md#desarrollo-en-windows)
