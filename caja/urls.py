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
]