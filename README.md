# organiza-te

Inventario, ventas y caja para pequeños comercios. Cada negocio tiene su catálogo, clientes, cuentas por cobrar y permisos de usuario. Los montos pueden consultarse en USD o en bolívares con la tasa BCV registrada.

## Desarrollo en Windows

Desde la carpeta que contiene `manage.py`, con Python 3.11 y Pipenv instalados, ejecuta:

```powershell
git switch rediseno/organiza-te
pipenv sync
pipenv run python manage.py migrate
pipenv run python manage.py runserver
```

Abre <http://localhost:8000/>. Para dar de alta un negocio, entra en <http://localhost:8000/usuarios/registro/>. La suite se ejecuta con `pipenv run python manage.py test`.

## Docker

En Windows, abre Docker Desktop y ejecuta `instalar.bat`. En Linux, ejecuta `./instalar.sh`. Los instaladores generan una clave de firma en el primer arranque y conservan el archivo `.env` en las siguientes ejecuciones. Por defecto, la aplicación escucha en el puerto 8000 de tu equipo.

SQLite se conserva en el volumen `inventario_data`; las fotos se guardan en `media/` junto a `compose.yaml`. Para recuperar un inventario con sus fotos necesitas ambas copias.

- [Instalación con Docker y acceso desde la red local](docs/INSTALACION.md)
- [Actualizar una instalación con datos y preparar la demo en Hostinger](docs/DEMO_HOSTINGER.md)

## Catálogo y carga por Excel

En **Productos → Cargar por Excel**, el propietario puede descargar su catálogo, una plantilla vacía o un ejemplo de papelería. Para crear un producto se requieren nombre, categoría y precio de venta en USD. Para actualizarlo basta el ID del catálogo o un código existente y la columna que cambia. Los códigos en formato de texto conservan sus ceros iniciales.

Los campos vacíos conservan los datos existentes. **Stock final** reemplaza la cantidad disponible. Revisa las diferencias y las categorías nuevas antes de confirmar. Si hay errores, la pantalla indica la fila y conserva el inventario. Puedes probar la demo con el ejemplo de papelería, que incluye un cuaderno y un servicio de copias.

[Inicio de sesión en móvil](docs/demo/login-movil.png) · [Revisión del Excel en escritorio](docs/demo/carga-excel.png) · [Modelo de inventario y migraciones](docs/MODULO_INVENTARIO.md)

## Estructura del proyecto

| Ruta | Contenido |
| --- | --- |
| `inventario/` | Configuración de Django, rutas y aplicación WSGI |
| `productos/`, `compras/`, `ventas/`, `caja/` | Catálogo, movimientos de inventario y operaciones del negocio |
| `clientes/`, `cuentas/`, `usuarios/` | Clientes, cobros, usuarios y acceso por módulo |
| `templates/`, `static/` | Plantillas compartidas, estilos, imágenes de marca y JavaScript |
| `Dockerfile`, `compose.yaml`, `docker/` | Construcción de la imagen, almacenamiento y arranque |
| `docs/` | Guías de instalación, actualización y despliegue |

La aplicación usa Django 5.2 LTS, SQLite y Bootstrap. La imagen ejecuta Gunicorn y sirve los archivos estáticos con WhiteNoise. [Licencia MIT](LICENSE)
