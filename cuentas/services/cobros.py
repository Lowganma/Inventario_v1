from django.core.exceptions import ValidationError
from django.db import transaction

from caja.services.caja import registrar_movimiento
from cuentas.models import Abono


@transaction.atomic
def registrar_abono_cuenta(
    *,
    cuenta,
    usuario,
    monto_pagado,
    fecha_pago,
    metodo,
    referencia="",
    notas="",
):
    """
    Registra un abono sobre una cuenta por cobrar.

    La operación actualiza el estado de la cuenta
    y registra automáticamente el ingreso correspondiente
    en el módulo de Caja.
    """

    # --------------------------------------------------------
    # VALIDACIONES
    # --------------------------------------------------------

    if monto_pagado <= 0:
        raise ValidationError(
            "El monto del abono debe ser mayor que cero."
        )

    if monto_pagado > cuenta.saldo_pendiente:
        raise ValidationError(
            (
                "El abono no puede superar el saldo pendiente "
                f"de ${cuenta.saldo_pendiente:.2f}."
            )
        )

    # --------------------------------------------------------
    # CREAR ABONO
    # --------------------------------------------------------

    abono = Abono.objects.create(
        cuenta=cuenta,
        monto_pagado=monto_pagado,
        fecha_pago=fecha_pago,
        metodo=metodo,
        referencia=referencia or "",
        notas=notas or "",
    )

    # --------------------------------------------------------
    # ACTUALIZAR ESTADO DE LA CUENTA
    # --------------------------------------------------------

    cuenta.refresh_from_db()

    if cuenta.saldo_pendiente <= 0:
        cuenta.estado = "pagada"
    else:
        cuenta.estado = "pendiente"

    cuenta.save(
        update_fields=[
            "estado",
        ]
    )

    # --------------------------------------------------------
    # REGISTRAR INGRESO EN CAJA
    # --------------------------------------------------------

    registrar_movimiento(
        negocio=cuenta.cliente.negocio,
        usuario=usuario,
        tipo="ingreso",
        monto=monto_pagado,
        metodo_pago=metodo,
        concepto=f"Abono cuenta #{cuenta.id}",
        origen="abono",
        referencia=(
            referencia
            or f"ABONO-{abono.id}"
        ),
        notas=(
            f"Ingreso automático correspondiente al "
            f"abono #{abono.id}."
        ),
    )

    return abono