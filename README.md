
```markdown
# 📦 Sistema de Gestión de Inventario y Caja (`Inventario_v1`)

Un sistema web modular, robusto y liviano desarrollado en **Django** para la administración de stock, control de ventas, caja chica y gestión de clientes en pequeños comercios y negocios locales.

---

## 🚀 Características Principales

El proyecto está diseñado de forma modular para facilitar su escalabilidad y mantenimiento:

* **📦 Inventario:** Control detallado de stock y movimientos de insumos en tiempo real.
* **🏷️ Productos:** Catálogo, presentación y categorización de mercancía.
* **💰 Caja:** Control de flujo de efectivo, aperturas y cierres de caja.
* **🛍️ Compras:** Registro de entradas de mercancía y gestión de compras.
* **👥 Clientes:** Registro y base de datos de clientes.
* **📊 Cuentas:** Módulo de seguimiento financiero interno.

---

## 🛠️ Tecnologías Utilizadas

* **Backend:** Python / Django
* **Frontend:** HTML5, CSS3, Bootstrap
* **Base de Datos:** SQLite (Entorno de desarrollo local)
* **Control de Versiones:** Git / GitHub

---

## 💻 Instalación y Configuración Local

Sigue estos pasos para ejecutar el proyecto en tu máquina local:

### 1. Clonar el repositorio
```bash
git clone [https://github.com/Lowganma/Inventario_v1.git](https://github.com/Lowganma/Inventario_v1.git)
cd Inventario_v1

```

### 2. Crear y activar entorno virtual

```bash
# En Windows:
python -m venv venv
.\venv\Scripts\activate

# En Linux/Mac:
python3 -m venv venv
source venv/bin/activate

```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt

```

### 4. Ejecutar migraciones y crear superusuario

```bash
python manage.py migrate
python manage.py createsuperuser

```

### 5. Iniciar el servidor

```bash
python manage.py runserver

```


---

## 📱 Acceso desde Red Local (Wi-Fi)

Para utilizar el sistema desde un teléfono celular o tablet dentro del mismo local:

1. Asegúrate de añadir la IP de la computadora host a `ALLOWED_HOSTS` en `settings.py`:
```python
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'TU_IP_LOCAL', '0.0.0.0']

```


2. Inicia el servidor escuchando en la red:
```bash
python manage.py runserver 0.0.0.0:8000

```


3. Ingresa desde el dispositivo móvil usando la dirección IP de la computadora: `http://TU_IP_LOCAL:8000/`.

---

## 📝 Licencia

Este proyecto se distribuye bajo la licencia **MIT**.
