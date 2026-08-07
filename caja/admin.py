from django.contrib import admin

from .models import MovimientoCaja


@admin.register(MovimientoCaja)
class MovimientoCajaAdmin(admin.ModelAdmin):
    """
    Administración de movimientos financieros.
    """

    list_display = [
        "fecha",
        "tipo",
        "concepto",
        "monto",
        "metodo_pago",
        "origen",
        "negocio",
    ]

    list_filter = [
        "tipo",
        "origen",
        "metodo_pago",
        "negocio",
    ]

    search_fields = [
        "concepto",
        "referencia",
    ]

    ordering = [
        "-fecha",
    ]