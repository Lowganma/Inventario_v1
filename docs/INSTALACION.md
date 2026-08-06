# Instalación de Inventario v1

Aplicación libre en Django para administrar clientes y cuentas por cobrar de
varios negocios. Los datos de cada negocio quedan aislados por usuario.

## Ejecutar con Docker

```bash
export DJANGO_SECRET_KEY="una-clave-larga-y-aleatoria"
docker compose up --build
```

Abra <http://localhost:8000/usuarios/registro/> para crear la primera cuenta.
El volumen `inventario_data` conserva la base SQLite entre reinicios.

## Desarrollo local

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Para ejecutar la suite:

```bash
python manage.py test
```

## Configuración

| Variable | Descripción |
| --- | --- |
| `DJANGO_SECRET_KEY` | Clave secreta; es obligatoria en una instalación pública. |
| `DJANGO_DEBUG` | Use `False` en producción. |
| `DJANGO_ALLOWED_HOSTS` | Hosts permitidos, separados por comas. |
| `SQLITE_PATH` | Ruta del archivo SQLite persistente. |

## Licencia

Distribuido bajo la licencia MIT. Consulte el archivo `LICENSE` en la raíz del
repositorio.
