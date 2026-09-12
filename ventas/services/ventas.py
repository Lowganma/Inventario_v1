from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import transaction

from caja.services.caja import registrar_movimiento
from cuentas.models import CuentaPorCobrar
from productos.models import Producto, PresentacionProducto
from ventas.models import DetalleVenta, Venta


DOS_DECIMALES = Decimal("0.01")


def _moneda(valor):
    return Decimal(valor).quantize(DOS_DECIMALES, rounding=ROUND_HALF_UP)


@transaction.atomic
def registrar_venta(
    *,
    negocio,
    usuario,
    cliente,
    tipo_pago,
    metodo_pago,
    referencia_pago,
    detalle_pago,
    tipo_descuento,
    valor_descuento,
    notas,
    detalles,
):
    valor_descuento = valor_descuento or Decimal("0.00")

    if tipo_pago == "fiado":
        if cliente is None:
            raise ValidationError("Debes seleccionar un cliente para una venta fiada.")
        if cliente.negocio_id != negocio.id:
            raise ValidationError("El cliente seleccionado no pertenece a este negocio.")
        metodo_pago = ""
        referencia_pago = ""
        detalle_pago = ""

    if tipo_pago != "fiado" and not metodo_pago:
        raise ValidationError("Debes seleccionar el método de pago.")

    if tipo_pago != "fiado" and metodo_pago == "transferencia" and not referencia_pago:
        raise ValidationError("Debes ingresar la referencia de la transferencia.")

    if tipo_pago != "fiado" and metodo_pago == "otro" and not detalle_pago:
        raise ValidationError("Debes describir el método de pago utilizado.")

    ultima_venta = Venta.objects.filter(negocio=negocio).order_by("-numero").first()
    siguiente_numero = ultima_venta.numero + 1 if ultima_venta and ultima_venta.numero else 1

    venta = Venta.objects.create(
        negocio=negocio,
        usuario=usuario,
        cliente=cliente,
        tipo_pago=tipo_pago,
        metodo_pago=metodo_pago,
        referencia_pago=referencia_pago or "",
        detalle_pago=detalle_pago or "",
        tipo_descuento=tipo_descuento or "",
        valor_descuento=valor_descuento,
        descuento=Decimal("0.00"),
        notas=notas or "",
        subtotal=Decimal("0.00"),
        total=Decimal("0.00"),
        estado="completada",
        numero=siguiente_numero,
    )

    subtotal_general = Decimal("0.00")
    lineas_creadas = 0

    for linea in detalles:
        if not linea or linea.get("DELETE"):
            continue

        producto = linea.get("producto")
        presentacion = linea.get("presentacion")
        cantidad = linea.get("cantidad")

        if producto is None:
            continue
        if cantidad is None or cantidad <= 0:
            raise ValidationError("Las cantidades deben ser mayores que cero.")

        producto_actual = (
            Producto.objects.select_for_update().get(
                id=producto.id,
                negocio=negocio,
                activo=True,
            )
        )

        factor_presentacion = Decimal("1.00")
        presentacion_actual = None
        cantidad_inventario = Decimal("0.00")

        if producto_actual.tipo == "producto":
            if presentacion is not None:
                presentacion_actual = (
                    PresentacionProducto.objects.select_for_update().get(
                        id=presentacion.id,
                        producto=producto_actual,
                        activa=True,
                    )
                )
                factor_presentacion = Decimal(presentacion_actual.cantidad_unidades)

            if producto_actual.unidad_base == "unidad" and cantidad != cantidad.to_integral_value():
                raise ValidationError(
                    f"La cantidad de {producto_actual.nombre} debe ser un número entero."
                )

            if (
                presentacion_actual
                and factor_presentacion != Decimal("1")
                and cantidad != cantidad.to_integral_value()
            ):
                raise ValidationError(
                    f"La cantidad de la presentación {presentacion_actual.nombre} debe ser entera."
                )

            cantidad_inventario = Decimal(cantidad) * factor_presentacion

            if producto_actual.stock < cantidad_inventario:
                raise ValidationError(
                    f"Stock insuficiente para {producto_actual.nombre}. Disponible: {producto_actual.stock}."
                )

            if presentacion_actual:
                if presentacion_actual.precio_venta is not None:
                    precio_unitario = presentacion_actual.precio_venta
                else:
                    precio_unitario = producto_actual.precio_venta * factor_presentacion
                costo_unitario = producto_actual.costo * factor_presentacion
            else:
                precio_unitario = producto_actual.precio_venta
                costo_unitario = producto_actual.costo
        else:
            presentacion_actual = None
            factor_presentacion = Decimal("1.00")
            cantidad_inventario = Decimal("0.00")
            precio_unitario = producto_actual.precio_venta
            costo_unitario = producto_actual.costo

        precio_unitario = _moneda(precio_unitario)
        costo_unitario = _moneda(costo_unitario)
        subtotal_linea = _moneda(Decimal(cantidad) * precio_unitario)

        DetalleVenta.objects.create(
            venta=venta,
            producto=producto_actual,
            presentacion=presentacion_actual,
            cantidad=cantidad,
            factor_presentacion=factor_presentacion,
            precio_unitario=precio_unitario,
            costo_unitario=costo_unitario,
            subtotal=subtotal_linea,
        )

        if producto_actual.tipo == "producto":
            producto_actual.stock -= cantidad_inventario
            producto_actual.save(update_fields=["stock", "fecha_actualizacion"])

        subtotal_general += subtotal_linea
        lineas_creadas += 1

    if lineas_creadas == 0:
        raise ValidationError("Debes agregar al menos un producto o servicio.")

    subtotal_general = _moneda(subtotal_general)
    descuento = Decimal("0.00")

    if tipo_descuento == "porcentaje":
        if valor_descuento <= 0 or valor_descuento > 100:
            raise ValidationError("El porcentaje de descuento debe estar entre 0 y 100.")
        descuento = _moneda(subtotal_general * valor_descuento / Decimal("100"))
    elif tipo_descuento == "fijo":
        if valor_descuento < 0:
            raise ValidationError("El descuento fijo no puede ser negativo.")
        descuento = _moneda(valor_descuento)
    elif tipo_descuento:
        raise ValidationError("El tipo de descuento no es válido.")

    if descuento > subtotal_general:
        raise ValidationError("El descuento no puede superar el subtotal.")

    total = _moneda(subtotal_general - descuento)

    venta.subtotal = subtotal_general
    venta.descuento = descuento
    venta.total = total
    venta.save(update_fields=["subtotal", "descuento", "total"])

    if tipo_pago == "fiado":
        cuenta = CuentaPorCobrar.objects.create(
            cliente=cliente,
            concepto=f"Venta #{venta.numero}",
            monto_total=total,
            estado="pendiente",
            notas=f"Cuenta generada automáticamente desde la venta #{venta.numero}.",
        )
        venta.cuenta_por_cobrar = cuenta
        venta.save(update_fields=["cuenta_por_cobrar"])
    else:
        notas_caja = "Ingreso generado automáticamente desde Ventas."
        if referencia_pago:
            notas_caja += f" Referencia: {referencia_pago}."
        if detalle_pago:
            notas_caja += f" Detalle: {detalle_pago}."

        registrar_movimiento(
            negocio=negocio,
            usuario=usuario,
            tipo="ingreso",
            monto=total,
            metodo_pago=metodo_pago,
            concepto=f"Venta #{venta.numero}",
            origen="venta",
            referencia=f"VENTA-{venta.id}",
            notas=notas_caja,
        )

    return venta
