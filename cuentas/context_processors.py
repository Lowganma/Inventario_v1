from .models import TasaCambio


def tasa_bcv_global(request):
    """
    Hace disponible la última tasa BCV en todas las plantillas.

    La variable se podrá utilizar como:
    {{ tasa_bcv_global }}
    """

    tasa = (
        TasaCambio.objects
        .filter(moneda="USD")
        .order_by("-fecha_vigencia", "-id")
        .first()
    )

    return {
        "tasa_bcv_global": tasa,
    }