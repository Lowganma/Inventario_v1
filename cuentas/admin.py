from django.contrib import admin

from .models import Abono, CuentaPorCobrar
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