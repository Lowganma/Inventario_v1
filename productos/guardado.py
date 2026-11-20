from django.db import transaction

from .models import PresentacionProducto


@transaction.atomic
def guardar_producto(producto, campos=None, precio_anterior=None):
    producto.save(update_fields=campos)
    if producto.tipo == "producto":
        # Puede haber otras presentaciones que también contengan una unidad.
        base = producto.presentaciones.filter(cantidad_unidades=1)
        if precio_anterior is not None and precio_anterior != producto.precio_venta:
            base.filter(nombre=producto.get_unidad_base_display(), precio_venta=precio_anterior).update(
                precio_venta=producto.precio_venta,
            )
        if not base.exists():
            PresentacionProducto.objects.create(
                producto=producto, cantidad_unidades=1,
                nombre=producto.get_unidad_base_display(), precio_venta=producto.precio_venta,
            )
