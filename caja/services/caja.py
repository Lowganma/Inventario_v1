from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.utils import timezone

from caja.models import CajaDiaria, MovimientoCaja


def _movimientos_fecha(negocio, fecha):
    return MovimientoCaja.objects.filter(negocio=negocio, fecha__date=fecha)


def obtener_resumen_caja(caja):
    """Calcula el cierre desde MovimientoCaja sin duplicar información."""
    movimientos = _movimientos_fecha(caja.negocio, caja.fecha)
    cero = Decimal("0.00")
    ingresos = movimientos.filter(tipo="ingreso").aggregate(total=Sum("monto"))["total"] or cero
    egresos = movimientos.filter(tipo="egreso").aggregate(total=Sum("monto"))["total"] or cero
    por_origen = {}
    for codigo, _ in MovimientoCaja.ORIGENES:
        por_origen[codigo] = movimientos.filter(origen=codigo).aggregate(total=Sum("monto"))["total"] or cero
    por_metodo = []
    for codigo, nombre in MovimientoCaja.METODOS_PAGO:
        qs = movimientos.filter(metodo_pago=codigo)
        entradas = qs.filter(tipo="ingreso").aggregate(total=Sum("monto"))["total"] or cero
        salidas = qs.filter(tipo="egreso").aggregate(total=Sum("monto"))["total"] or cero
        por_metodo.append({"codigo": codigo, "nombre": nombre, "ingresos": entradas, "egresos": salidas, "saldo": entradas - salidas})
    return {
        "movimientos": movimientos.select_related("usuario"), "ingresos": ingresos,
        "egresos": egresos, "saldo_final_sistema": caja.saldo_inicial + ingresos - egresos,
        "ventas_contado": por_origen["venta"], "abonos": por_origen["abono"],
        "compras": por_origen["compra"],
        "ingresos_manuales": movimientos.filter(origen="manual", tipo="ingreso").aggregate(total=Sum("monto"))["total"] or cero,
        "egresos_manuales": movimientos.filter(origen="manual", tipo="egreso").aggregate(total=Sum("monto"))["total"] or cero,
        "por_metodo": por_metodo,
    }


@transaction.atomic
def abrir_caja(*, negocio, usuario, saldo_inicial, notas="", fecha=None):
    fecha = fecha or timezone.localdate()
    try:
        return CajaDiaria.objects.create(negocio=negocio, fecha=fecha, saldo_inicial=saldo_inicial, abierta_por=usuario, notas=notas or "")
    except IntegrityError as error:
        raise ValidationError("Ya existe una caja para esta fecha.") from error


@transaction.atomic
def cerrar_caja(*, caja, usuario, saldo_final_declarado, notas=""):
    caja = CajaDiaria.objects.select_for_update().get(pk=caja.pk, negocio=caja.negocio)
    if caja.estado == "cerrada":
        raise ValidationError("Esta caja ya fue cerrada.")
    resumen = obtener_resumen_caja(caja)
    caja.saldo_final_sistema = resumen["saldo_final_sistema"]
    caja.saldo_final_declarado = Decimal(saldo_final_declarado)
    caja.diferencia = caja.saldo_final_declarado - caja.saldo_final_sistema
    caja.estado = "cerrada"
    caja.fecha_cierre = timezone.now()
    caja.cerrada_por = usuario
    if notas:
        caja.notas = "\n".join(filter(None, [caja.notas, notas]))
    caja.save()
    return caja


@transaction.atomic
def registrar_movimiento(
    *,
    negocio,
    usuario,
    tipo,
    monto,
    metodo_pago,
    concepto,
    origen="manual",
    referencia="",
    notas="",
):
    """
    Registra una entrada o salida monetaria.

    Esta función constituye el punto central de integración
    entre Caja y los demás módulos del sistema.
    """

    monto = Decimal(monto)

    if monto <= 0:
        raise ValidationError(
            "El monto del movimiento debe ser mayor que cero."
        )

    if tipo not in {
        "ingreso",
        "egreso",
    }:
        raise ValidationError(
            "El tipo de movimiento no es válido."
        )

    # Toda integración financiera usa la jornada vigente como frontera.
    caja = CajaDiaria.objects.filter(negocio=negocio, fecha=timezone.localdate()).first()
    if caja is None:
        raise ValidationError("Debes abrir la caja de hoy antes de registrar movimientos.")
    if caja.estado == "cerrada":
        raise ValidationError("La caja de hoy está cerrada y no admite movimientos.")

    movimiento = MovimientoCaja.objects.create(
        negocio=negocio,
        usuario=usuario,
        tipo=tipo,
        origen=origen,
        monto=monto,
        metodo_pago=metodo_pago,
        concepto=concepto,
        referencia=referencia or "",
        notas=notas or "",
    )

    return movimiento
