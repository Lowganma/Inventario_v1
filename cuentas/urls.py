from django.urls import path

from . import views


app_name = "cuentas"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("", views.lista_cuentas, name="lista"),
    path("nueva/", views.crear_cuenta, name="crear"),

    path(
        "<int:cuenta_id>/abono/",
        views.registrar_abono,
        name="registrar_abono",
    ),

    path(
        "<int:cuenta_id>/pagar-completo/",
        views.pagar_cuenta_completa,
        name="pagar_completo",
    ),

    path(
        "<int:cuenta_id>/",
        views.detalle_cuenta,
        name="detalle",
    ),
    path(
    "<int:cuenta_id>/anular/",
    views.anular_cuenta,
    name="anular",
    ),
]