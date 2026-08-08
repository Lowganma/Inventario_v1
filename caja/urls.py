from django.urls import path

from . import views


app_name = "caja"


urlpatterns = [
    path(
        "",
        views.dashboard_caja,
        name="dashboard",
    ),
    path(
        "movimientos/",
        views.lista_movimientos,
        name="movimientos",
    ),
    path(
        "movimientos/nuevo/",
        views.crear_movimiento,
        name="crear_movimiento",
    ),
    path("abrir/", views.abrir_caja_view, name="abrir"),
    path("cerrar/", views.cerrar_caja_view, name="cerrar"),
    path("cierres/", views.lista_cierres, name="cierres"),
    path("cierres/<int:caja_id>/", views.detalle_cierre, name="detalle_cierre"),
]
