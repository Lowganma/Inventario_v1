# Guía fácil de instalación y despliegue

Esta guía está pensada para instalar **Inventario v1** sin conocer Python ni
Django. Con Docker no hace falta instalar manualmente Django, Gunicorn ni
WhiteNoise: todo queda dentro del contenedor.

> **¿Qué es WhiteNoise?** Es la pieza que entrega el CSS y JavaScript de la
> aplicación cuando se ejecuta en producción. Ya está incluido en
> `requirements.txt`; quien use Docker no tiene que instalarlo por separado.

## Opción 1 — Windows, instalación tipo «siguiente, siguiente»

### Paso 1. Instalar Docker Desktop

1. Descarga e instala **Docker Desktop**.
2. Acepta las opciones predeterminadas del instalador.
3. Reinicia Windows si el instalador lo solicita.
4. Abre Docker Desktop y espera a que indique que está funcionando.

### Paso 2. Descargar la aplicación

Descarga el proyecto como ZIP, descomprímelo y abre la carpeta resultante. No
lo ejecutes directamente dentro del ZIP.

### Paso 3. Instalar

Haz doble clic en **`instalar.bat`**. El instalador:

1. crea una configuración privada y una clave aleatoria;
2. construye la imagen;
3. crea la base de datos;
4. inicia la aplicación;
5. abre la página de registro.

La primera instalación puede tardar varios minutos. Las siguientes serán más
rápidas. Registra el primer usuario en:
<http://localhost:8000/usuarios/registro/>.

### Uso diario

Docker puede iniciar los contenedores automáticamente. Si la aplicación está
apagada, abre una terminal en la carpeta y ejecuta:

```powershell
docker compose up -d
```

Para apagarla:

```powershell
docker compose stop
```

No uses `docker compose down -v`: la opción `-v` elimina el volumen donde vive
la base de datos.

## Opción 2 — Linux, servidor o Raspberry Pi de 64 bits

Instala Docker Engine con el procedimiento de tu distribución. Después:

```bash
git clone URL_DEL_REPOSITORIO inventario
cd inventario
chmod +x instalar.sh
./instalar.sh
```

Abre <http://localhost:8000/usuarios/registro/>. Si el servidor no tiene
navegador, utiliza su IP desde otro equipo, por ejemplo
`http://192.168.1.50:8000`.

## Permitir acceso desde otros equipos de la oficina

1. Averigua la IP local del equipo donde está Docker, por ejemplo
   `192.168.1.50`.
2. Abre `.env` con un editor de texto.
3. Agrega esa IP a `DJANGO_ALLOWED_HOSTS`:

```dotenv
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.50
```

4. Aplica el cambio:

```bash
docker compose up -d
```

5. En los demás equipos abre `http://192.168.1.50:8000`.

Puede ser necesario permitir el puerto 8000 en el firewall. Para una oficina,
asigna una IP fija al servidor desde el router para que la dirección no cambie.

## Publicar en un VPS o proveedor de contenedores

La opción más sencilla es usar un proveedor que acepte un `Dockerfile` o
Docker Compose:

1. Sube este repositorio al proveedor.
2. Selecciona **Dockerfile** como tipo de aplicación, o usa `compose.yaml` si el
   proveedor admite Docker Compose.
3. Crea almacenamiento persistente y móntalo en **`/app/data`**. Sin este paso,
   los datos se perderán al reemplazar el contenedor.
4. Configura estas variables:

```dotenv
DJANGO_SECRET_KEY=una-clave-muy-larga-y-aleatoria
DJANGO_ALLOWED_HOSTS=cuentas.ejemplo.com
CSRF_TRUSTED_ORIGINS=https://cuentas.ejemplo.com
SQLITE_PATH=/app/data/db.sqlite3
```

5. Expón el puerto **8000** y conecta el dominio.
6. Activa HTTPS desde el panel del proveedor.
7. Abre `https://cuentas.ejemplo.com/usuarios/registro/`.

No publiques el archivo `.env`, no uses `DJANGO_DEBUG=True` y no copies la
clave de ejemplo en un servidor real.

### Servidor propio con Docker Compose

En un VPS administrado por ti:

```bash
git clone URL_DEL_REPOSITORIO inventario
cd inventario
cp .env.example .env
nano .env
docker compose up -d --build
```

Cambia en `.env` la clave, el dominio permitido y el origen HTTPS. Coloca un
proxy HTTPS (por ejemplo, el que ya proporcione tu panel de servidor) delante
del puerto 8000. No expongas el panel de administración sin HTTPS.

## Copias de seguridad

Los datos están en el volumen `inventario_data`. Para crear una copia portátil
de SQLite sin detener la aplicación:

```bash
mkdir -p copias
docker compose exec -T web python -c "import sqlite3; origen=sqlite3.connect('/app/data/db.sqlite3'); copia=sqlite3.connect('/app/data/copia.sqlite3'); origen.backup(copia); copia.close(); origen.close()"
docker compose cp web:/app/data/copia.sqlite3 ./copias/inventario.sqlite3
```

Guarda `copias/inventario.sqlite3` fuera del equipo. Para restaurarla, detén la
aplicación y copia el archivo:

```bash
docker compose stop
docker compose cp ./copias/inventario.sqlite3 web:/app/data/db.sqlite3
docker compose start
```

Haz una copia antes de cada actualización.

## Actualizar

Si instalaste con Git:

```bash
git pull
docker compose up -d --build
```

Si descargaste un ZIP, conserva `.env` y la carpeta anterior hasta confirmar
que la nueva versión funciona. El volumen de Docker mantiene la base de datos.

## Comandos de diagnóstico

```bash
# Ver si está funcionando
docker compose ps

# Ver errores recientes
docker compose logs --tail=100 web

# Reiniciar
docker compose restart web

# Comprobar Django dentro del contenedor
docker compose exec web python manage.py check
```

Problemas habituales:

- **Docker no se reconoce:** instala o abre Docker Desktop.
- **El puerto 8000 está ocupado:** cambia `APP_PORT=8001` en `.env` y abre
  `http://localhost:8001`.
- **DisallowedHost:** agrega la IP o dominio a `DJANGO_ALLOWED_HOSTS` en `.env`.
- **CSRF verification failed usando HTTPS:** agrega la URL completa, incluido
  `https://`, a `CSRF_TRUSTED_ORIGINS`.
- **La página aparece sin estilos:** reconstruye con
  `docker compose up -d --build`; WhiteNoise sirve los archivos recopilados al
  iniciar el contenedor.

## Instalación sin Docker, solo para desarrolladores

```bash
python -m venv .venv
. .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

En esta modalidad sí debes instalar las dependencias de `requirements.txt`,
incluido WhiteNoise. Para clientes finales se recomienda Docker.
