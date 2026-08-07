from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from cuentas.models import CuentaPorCobrar
from productos.models import Producto

from ventas.models import Venta, DetalleVenta


@transaction.atomic
def registrar_venta(
    *,
    negocio,
    usuario,
    cliente,
    tipo_pago,
    descuento,
    notas,
    detalles,
):
    """
    Registra una venta completa.

    La operación se ejecuta dentro de una transacción para
    garantizar que la venta y la modificación del inventario
    ocurran juntas o no ocurran.
    """

    descuento = descuento or Decimal("0.00")


    # --------------------------------------------------------
    # VALIDACIÓN DE CLIENTE PARA FIADOS
    # --------------------------------------------------------

    if tipo_pago == "fiado":

        if cliente is None:
            raise ValidationError(
                "Debes seleccionar un cliente para una venta fiada."
            )

        if cliente.negocio_id != negocio.id:
            raise ValidationError(
                "El cliente seleccionado no pertenece a este negocio."
            )


    # --------------------------------------------------------
    # CREAR CABECERA DE LA VENTA
    # --------------------------------------------------------

    venta = Venta.objects.create(
        negocio=negocio,
        usuario=usuario,
        cliente=cliente,
        tipo_pago=tipo_pago,
        descuento=descuento,
        notas=notas or "",
        subtotal=Decimal("0.00"),
        total=Decimal("0.00"),
        estado="completada",
    )


    subtotal_general = Decimal("0.00")
    lineas_creadas = 0


    # --------------------------------------------------------
    # PRODUCTOS DE LA VENTA
    # --------------------------------------------------------

    for linea in detalles:

        if not linea:
            continue

        if linea.get("DELETE"):
            continue

        producto = linea.get("producto")
        cantidad = linea.get("cantidad")

        if producto is None:
            continue

        if cantidad is None or cantidad <= 0:
            raise ValidationError(
                "Las cantidades deben ser mayores que cero."
            )


        # ----------------------------------------------------
        # BLOQUEAR PRODUCTO
        # ----------------------------------------------------

        producto_actual = (
            Producto.objects
            .select_for_update()
            .get(
                id=producto.id,
                negocio=negocio,
                activo=True,
            )
        )


        # ----------------------------------------------------
        # VALIDAR STOCK REAL
        # ----------------------------------------------------

        if producto_actual.stock < cantidad:

            raise ValidationError(
                (
                    f"Stock insuficiente para "
                    f"{producto_actual.nombre}. "
                    f"Disponible: {producto_actual.stock}."
                )
            )


        """
        El precio confiable se toma del producto almacenado,
        no del navegador.
        """

        precio_unitario = producto_actual.precio_venta
        costo_unitario = producto_actual.costo

        subtotal_linea = (
            Decimal(cantidad)
            * precio_unitario
        )


        # ----------------------------------------------------
        # GUARDAR DETALLE HISTÓRICO
        # ----------------------------------------------------

        DetalleVenta.objects.create(
            venta=venta,
            producto=producto_actual,
            cantidad=cantidad,
            precio_unitario=precio_unitario,
            costo_unitario=costo_unitario,
            subtotal=subtotal_linea,
        )


        # ----------------------------------------------------
        # DESCONTAR INVENTARIO
        # ----------------------------------------------------

        producto_actual.stock -= cantidad

        producto_actual.save(
            update_fields=[
                "stock",
                "fecha_actualizacion",
            ]
        )


        subtotal_general += subtotal_linea
        lineas_creadas += 1


    if lineas_creadas == 0:

        raise ValidationError(
            "Debes agregar al menos un producto."
        )


    # --------------------------------------------------------
    # TOTAL DE LA VENTA
    # --------------------------------------------------------

    if descuento > subtotal_general:

        raise ValidationError(
            "El descuento no puede superar el subtotal."
        )


    total = (
        subtotal_general
        - descuento
    )


    venta.subtotal = subtotal_general
    venta.total = total

    venta.save(
        update_fields=[
            "subtotal",
            "total",
        ]
    )


    # --------------------------------------------------------
    # GENERAR CUENTA POR COBRAR
    # --------------------------------------------------------

    if tipo_pago == "fiado":

        cuenta = CuentaPorCobrar.objects.create(
            cliente=cliente,
            concepto=f"Venta #{venta.id}",
            monto_total=total,
            estado="pendiente",
            notas=(
                f"Cuenta generada automáticamente "
                f"desde la venta #{venta.id}."
            ),
        )

        venta.cuenta_por_cobrar = cuenta

        venta.save(
            update_fields=[
                "cuenta_por_cobrar",
            ]
        )


    return venta