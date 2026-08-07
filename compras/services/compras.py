from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from productos.models import Producto

from compras.models import Compra, DetalleCompra
from caja.services.caja import registrar_movimiento

@transaction.atomic
def registrar_compra(
    *,
    negocio,
    usuario,
    metodo_pago,
    notas,
    detalles,
):
    """
    Registra una compra completa y actualiza el inventario.

    La operación es atómica:
    si ocurre cualquier error, no se guarda una compra parcial
    ni se actualiza parcialmente el stock.
    """

    compra = Compra.objects.create(
        negocio=negocio,
        usuario=usuario,
        metodo_pago=metodo_pago,
        notas=notas or "",
        total=Decimal("0.00"),
    )

    total_compra = Decimal("0.00")
    lineas_creadas = 0

    for linea in detalles:

        if not linea:
            continue

        if linea.get("DELETE"):
            continue

        producto = linea.get("producto")
        cantidad = linea.get("cantidad")
        precio_compra = linea.get("precio_compra")
        precio_venta = linea.get("precio_venta")

        if not producto:
            continue

        # Seguridad multiempresa.
        if producto.negocio_id != negocio.id:
            raise ValidationError(
                "Uno de los productos no pertenece a este negocio."
            )

        if cantidad is None or cantidad <= 0:
            raise ValidationError(
                f"La cantidad de {producto.nombre} debe ser mayor que cero."
            )

        if precio_compra is None or precio_compra < 0:
            raise ValidationError(
                f"El precio de compra de {producto.nombre} no es válido."
            )

        if precio_venta is None or precio_venta < 0:
            raise ValidationError(
                f"El precio de venta de {producto.nombre} no es válido."
            )

        # Bloqueamos la fila mientras modificamos existencias.
        producto_bloqueado = (
            Producto.objects
            .select_for_update()
            .get(
                pk=producto.pk,
                negocio=negocio,
            )
        )

        subtotal = (
            Decimal(cantidad)
            * precio_compra
        )

        DetalleCompra.objects.create(
            compra=compra,
            producto=producto_bloqueado,
            cantidad=cantidad,
            precio_compra=precio_compra,
            precio_venta=precio_venta,
            subtotal=subtotal,
        )

        # La compra repone existencias.
        producto_bloqueado.stock += cantidad

        # Regla inicial:
        # el último precio registrado pasa a ser el costo
        # y precio de venta vigente del producto.
        producto_bloqueado.costo = precio_compra
        producto_bloqueado.precio_venta = precio_venta

        producto_bloqueado.save(
            update_fields=[
                "stock",
                "costo",
                "precio_venta",
                "fecha_actualizacion",
            ]
        )

        total_compra += subtotal
        lineas_creadas += 1

    if lineas_creadas == 0:
        raise ValidationError(
            "Debes agregar al menos un producto a la compra."
        )

    compra.total = total_compra
    compra.save(
        update_fields=[
            "total",
        ]
    )

    # ============================================================
# REGISTRO AUTOMÁTICO EN CAJA
# ============================================================

    registrar_movimiento(
        negocio=negocio,
        usuario=usuario,
        tipo="egreso",
        monto=total_compra,
        metodo_pago=metodo_pago,
        concepto=f"Compra #{compra.id}",
        origen="compra",
        referencia=f"COMPRA-{compra.id}",
        notas="Egreso generado automáticamente desde Compras.",
    )





    return compra