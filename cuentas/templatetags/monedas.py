from django import template
from django.template.defaultfilters import floatformat
from django.utils.html import format_html

register = template.Library()


@register.simple_tag
def importe(valor):
    """Conserva el importe original en USD para cambiar solo su presentación."""
    if valor is None or valor == "":
        return "—"
    return format_html(
        '<data class="ot-importe" value="{}">USD {}</data>',
        format(valor, "f"), floatformat(valor, 2),
    )
