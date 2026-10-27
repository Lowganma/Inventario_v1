from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django import template
from django.utils.html import format_html

register = template.Library()


def importe(valor):
    return Decimal(str(valor)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def formato_bs(valor):
    return format(valor, ",.2f").translate(str.maketrans({",": ".", ".": ","}))


@register.simple_tag(takes_context=True)
def precio_moneda(context, valor):
    """Equivalente de referencia con la tasa actual; no cambia montos contables."""
    usd = importe(valor)
    tasa = context.get("tasa_bcv_global")
    try:
        cambio = Decimal(str(tasa.valor)) if tasa else Decimal("0")
        disponible = cambio.is_finite() and cambio > 0
    except (InvalidOperation, AttributeError):
        disponible = False
    if disponible:
        bs = formato_bs(importe(usd * cambio))
        secundario = f"Bs. {bs}"
        referencia = f"Referencia BCV del {tasa.fecha_vigencia:%d/%m/%Y}: 1 USD = Bs. {formato_bs(cambio)}"
    else:
        secundario = "Tasa BCV no disponible"
        referencia = "Registra una tasa BCV válida para ver el equivalente en bolívares"
    return format_html(
        '<span class="importe-moneda" data-importe-usd="{}" title="{}">'
        '<span class="importe-usd">${}</span><span class="importe-bs">{}</span></span>',
        format(usd, ".2f"), referencia, format(usd, ".2f"), secundario,
    )
