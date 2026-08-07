from django.contrib import admin

from .models import Categoria, Producto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "negocio", "activa", "fecha_creacion")
    search_fields = ("nombre", "descripcion", "negocio__nombre")
    list_filter = ("activa", "negocio")


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "codigo",
        "negocio",
        "categoria",
        "stock",
        "stock_minimo",
        "activo",
    )
    search_fields = ("nombre", "codigo", "categoria__nombre", "negocio__nombre")
    list_filter = ("activo", "categoria", "negocio")
