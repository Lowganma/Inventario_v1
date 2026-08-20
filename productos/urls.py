from django.urls import path

from . import views

app_name = "productos"

urlpatterns = [
    path("", views.index, name="index"),
    path("nuevo/", views.crear_producto, name="crear"),
    path("categorias/", views.lista_categorias, name="categorias"),
    path("categorias/nueva/", views.crear_categoria, name="crear_categoria"),
    path(
    "categorias/crear-rapida/",
    views.crear_categoria_rapida,
    name="crear_categoria_rapida",
    ),
    path(
        "categorias/<int:categoria_id>/editar/",
        views.editar_categoria,
        name="editar_categoria",
    ),
    path(
    "<int:producto_id>/datos/",
    views.datos_producto,
    name="datos_producto",
    ),
    path("<int:producto_id>/", views.detalle, name="detalle"),
    path("<int:producto_id>/editar/", views.editar_producto, name="editar"),
]
