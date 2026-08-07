# Módulo de inventario

La app independiente `productos` permite organizar el inventario mediante categorías y productos. Cada producto registra stock actual, stock mínimo, costo, precio de venta y estado activo o inactivo. El listado señala las existencias bajas y calcula el valor estimado disponible.

Las categorías y los productos están asociados obligatoriamente al `Negocio` del usuario autenticado. Las vistas, los formularios y las consultas filtran por ese negocio para impedir que una empresa consulte o modifique información de otra.

## Actualización de datos antiguos

La migración `0003_preparar_inventario` agrega temporalmente la asociación opcional. Si existe un único negocio, `0004_asociar_datos_existentes` vincula automáticamente los registros anteriores.

Si existen varios negocios y datos antiguos sin dueño, ejecuta primero:

```bash
python manage.py migrate productos 0003
python manage.py shell
```

En el shell, asigna de forma controlada `negocio_id` a cada `Categoria` y `Producto` según su propietario real. Después completa las migraciones:

```bash
python manage.py migrate
```

La migración `0005_finalizar_inventario` hará obligatoria la asociación.
