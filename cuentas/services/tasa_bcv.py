from datetime import date
from decimal import Decimal, InvalidOperation

import requests
from django.utils.dateparse import parse_date

from cuentas.models import TasaCambio


BCV_API_URL = "https://bcv.today/api/v1/rate.json"


class ErrorConsultaBCV(Exception):
    """Error controlado al consultar la tasa USD."""


def consultar_tasa_dolar_bcv():
    """
    Consulta únicamente la tasa USD publicada por la API.

    Devuelve:
        valor: Decimal
        fecha_vigencia: date
    """

    try:
        respuesta = requests.get(
            BCV_API_URL,
            timeout=15,
            headers={
                "Cache-Control": "no-cache",
                "User-Agent": "ControlDeCuentas/1.0",
            },
        )

        respuesta.raise_for_status()
        datos = respuesta.json()

    except requests.RequestException as error:
        raise ErrorConsultaBCV(
            f"No fue posible consultar la API: {error}"
        ) from error

    except ValueError as error:
        raise ErrorConsultaBCV(
            "La API devolvió una respuesta que no es JSON válido."
        ) from error

    try:
        valor = Decimal(str(datos["USD"]))

    except (KeyError, InvalidOperation, TypeError) as error:
        raise ErrorConsultaBCV(
            "La respuesta no contiene una tasa USD válida."
        ) from error

    fecha_vigencia = parse_date(
        datos.get("effective_date")
        or datos.get("date")
        or ""
    )

    if fecha_vigencia is None:
        fecha_vigencia = date.today()

    return valor, fecha_vigencia


def actualizar_tasa_dolar_bcv():
    """
    Consulta la tasa USD y la guarda o actualiza en la base de datos.
    """

    valor, fecha_vigencia = consultar_tasa_dolar_bcv()

    tasa, creada = TasaCambio.objects.update_or_create(
        moneda="USD",
        fecha_vigencia=fecha_vigencia,
        defaults={
            "valor": valor,
            "fuente": "BCV Today / datos BCV",
        },
    )

    return tasa, creada