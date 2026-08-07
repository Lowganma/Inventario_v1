from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from caja.models import MovimientoCaja


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