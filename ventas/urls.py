from django.urls import path

from . import views


app_name = "ventas"


urlpatterns = [
    path(
        "",
        views.lista_ventas,
        name="lista",
    ),
    path(
        "nueva/",
        views.crear_venta,
        name="crear",
    ),
    path(
    "producto/<int:producto_id>/datos/",
    views.datos_producto,
    name="datos_producto",
    ),
    path(
        "<int:venta_id>/",
        views.detalle_venta,
        name="detalle",
    ),
    
]
