from django.contrib import admin

from .models import Abono, CuentaPorCobrar, TasaCambio
# Register your models here.

@admin.register(CuentaPorCobrar)
class CuentaPorCobrarAdmin(admin.ModelAdmin):
    list_display = (
        "cliente",
        "concepto",
        "monto_total",
        "total_abonado",
        "saldo_pendiente",
        "estado",
    )


@admin.register(Abono)
class AbonoAdmin(admin.ModelAdmin):
    list_display = (
        "cuenta",
        "monto_pagado",
        "fecha_pago",
        "metodo",
    )

@admin.register(TasaCambio)
class TasaCambioAdmin(admin.ModelAdmin):
    list_display = [
        "moneda",
        "valor",
        "fecha_vigencia",
        "fecha_actualizacion",
        "fuente",
    ]

    list_filter = [
        "moneda",
        "fecha_vigencia",
    ]

    search_fields = [
        "moneda",
        "fuente",
    ]

    ordering = [
        "-fecha_vigencia",
        "-id",
    ]