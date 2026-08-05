from django.contrib import admin

from .models import Negocio


@admin.register(Negocio)
class NegocioAdmin(admin.ModelAdmin):
    list_display = [
        "nombre",
        "propietario",
        "telefono",
        "fecha_registro",
    ]

    search_fields = [
        "nombre",
        "propietario__username",
        "propietario__email",
    ]