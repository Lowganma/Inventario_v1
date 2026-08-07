from django.urls import path, include

from . import views

app_name = "compras"

urlpatterns = [
    path("", 
         views.lista_compras,
         name="lista"
    ),
    path("nueva/", 
         views.crear_compra,
         name="crear"
    ),
    path("<int:compra_id>/", 
         views.detalle_compra,
         name="detalle"
    ),
]