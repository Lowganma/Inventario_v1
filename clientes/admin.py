from django.contrib import admin

from .models import Cliente, Pago


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    """
    Configura cómo se muestran y administran los clientes
    desde el panel administrativo de Django.
    """

    list_display = [
        "nombre",
        "apellido",
        "telefono",
        "negocio",
        "estado",
    ]

    list_filter = [
        "negocio",
        "estado",
    ]

    search_fields = [
        "nombre",
        "apellido",
        "telefono",
        "negocio__nombre",
    ]


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = [
        "cliente",
        "monto_pagado",
        "fecha_pago",
        "metodo",
    ]