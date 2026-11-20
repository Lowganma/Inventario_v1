# Preparar una demo de organiza-te

## Probar la recuperación en Windows

En la carpeta del proyecto ejecuta `pipenv run python manage.py runserver`. Cierra la sesión, abre **¿Olvidaste tu contraseña?** e introduce el correo de un usuario de prueba activo. Con el modo de desarrollo y sin EMAIL_HOST, Django imprime el mensaje en esa misma terminal. Copia el enlace completo al navegador. Caduca al cabo de una hora y deja de servir al guardar una nueva contraseña.

Los nuevos empleados y propietarios registran un correo. Si una cuenta antigua carece de correo, un superusuario de confianza puede completarlo desde **Administración de Django → Usuarios**, después de verificar con su titular la dirección correcta.

## Actualizar una instalación con datos

**Si usas Pipenv en Windows**, detén el servidor y haz una copia de `db.sqlite3` y de la carpeta `media/`. Ejecuta estos comandos desde la rama `rediseno/organiza-te`.

```powershell
git pull --ff-only
pipenv sync
pipenv run python manage.py migrate
pipenv run python manage.py runserver
```

La carpeta de fotos y las rutas guardadas en los productos siguen siendo las mismas.

**Si ya subiste fotos con una versión anterior de Docker**, rescátalas antes de recrear o quitar el contenedor anterior. En PowerShell, desde la carpeta de Compose, usa una carpeta de respaldo nueva. Detener el servicio deja estable la copia de SQLite y conserva el contenedor para copiar sus archivos.

```powershell
$respaldo = "../respaldo-organiza-te-$(Get-Date -Format yyyyMMdd-HHmmss)"
New-Item -ItemType Directory -Path "$respaldo/media" -Force
docker compose stop web
docker compose cp web:/app/data/. "$respaldo"
docker compose cp web:/app/media/. "$respaldo/media"
```

Comprueba que el respaldo contiene `db.sqlite3` y las imágenes esperadas. Copia el contenido de `$respaldo/media` a `media/` junto a `compose.yaml`, conservando la subcarpeta `productos/`. Si ya tienes archivos locales con los mismos nombres, compara ambas copias antes de sobrescribirlos. Si no llegaste a subir fotos en Docker, la carpeta del contenedor puede no existir.

Actualiza la rama y ejecuta `docker compose up -d --build` desde la misma carpeta y con el mismo nombre de proyecto de Compose. Se reutiliza el volumen de la base `inventario_data`. El contenedor monta la carpeta `./media` del equipo en `/app/media`. Para verificarlo, sube una foto a un producto de prueba, ejecuta `docker compose up -d --force-recreate web` y vuelve a abrir la ficha. Al trasladar la demo a otro VPS, restaura tanto la base como `media/`; la opción `docker compose down -v` elimina el volumen de la base.

## Alojar la app

Hostinger ofrece ejecución de Django en VPS. Puedes mantener el portafolio Astro en Business y apuntar el registro DNS A de un subdominio, por ejemplo organiza-te.lowganma.com, a la IP del VPS. El proyecto usa Django 5.2 LTS, Gunicorn y Docker Compose con Python 3.11.

1. Crea un negocio de demostración con datos ficticios, separado de tu inventario real. Define cómo se restablecerán los datos entre visitas. La app permite el registro público y la carga de archivos. Para una demo pública, delimita quién puede registrarse y limita las solicitudes de inicio de sesión, recuperación y las cargas en el proxy.
2. Configura HTTPS con Caddy o Nginx. El proxy debe reemplazar la cabecera X-Forwarded-Proto y redirigir HTTP a HTTPS. Expón solo el proxy al público. La configuración Compose del repositorio publica el puerto de la app. Si el proxy corre en el host, enlaza ese puerto a 127.0.0.1 antes de habilitar DJANGO_TRUST_HTTPS_PROXY=1.
3. Crea en el servidor un .env privado con una DJANGO_SECRET_KEY aleatoria y estable, DJANGO_ALLOWED_HOSTS con el subdominio exacto y CSRF_TRUSTED_ORIGINS con la URL HTTPS. El servicio Compose ya define DJANGO_DEBUG=False. Activa DJANGO_TRUST_HTTPS_PROXY=1 solo tras configurar el proxy del paso anterior.
4. Para Hostinger Email, copia los datos del buzón desde hPanel. Configura EMAIL_HOST=smtp.hostinger.com, EMAIL_PORT=465 (SSL), EMAIL_HOST_USER con la dirección completa, EMAIL_HOST_PASSWORD con la contraseña del buzón y DEFAULT_FROM_EMAIL con esa misma dirección. También puedes usar 587 con STARTTLS. Si usas otro proveedor, usa sus datos SMTP. En desarrollo con Pipenv estas variables se pueden poner en el .env local. En Docker se pasan al contenedor desde Compose.
5. Envía también las solicitudes de `/media/` a la aplicación. Django entrega las fotos a los usuarios del negocio y WhiteNoise sirve `/static/`. Haz copias periódicas de SQLite y de la carpeta `media/` del servidor.
6. Ejecuta las pruebas antes de desplegar y `docker compose exec web python manage.py check --deploy` con la configuración real. Prueba una recuperación con un buzón que controles, confirma que recibes un enlace HTTPS del subdominio y que el enlace deja de funcionar después del cambio. Verifica también que una foto siga visible al recrear el contenedor.

[Frameworks compatibles con Hostinger](https://www.hostinger.com/support/which-programming-languages-and-frameworks-are-supported-at-hostinger/) · [Configuración del correo](https://www.hostinger.com/support/1575756-how-to-get-email-account-configuration-details-for-hostinger-email/) · [Versiones soportadas de Django](https://www.djangoproject.com/download/)
