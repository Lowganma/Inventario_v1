from django.urls import path

from . import views


app_name = "usuarios"

urlpatterns = [
    path(
        "registro/",
        views.registro,
        name="registro",
    ),
    path("lista/", views.lista_usuarios, name="lista"),
    path("nuevo/", views.crear_usuario, name="crear"),
    path("<int:perfil_id>/rol/", views.editar_rol, name="editar_rol"),
    path("modulos/", views.configurar_modulos, name="modulos"),
]
