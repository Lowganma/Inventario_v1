from django.core.exceptions import ValidationError
from django.db import transaction

from .models import MODULOS_DISPONIBLES, ModuloNegocio


DEPENDENCIAS_MODULOS = {"ventas": "inventario", "compras": "inventario"}


@transaction.atomic
def actualizar_modulos(*, negocio, seleccionados):
    """Valida dependencias y actualiza únicamente la configuración del negocio."""
    seleccionados = set(seleccionados)
    errores = []
    for modulo, dependencia in DEPENDENCIAS_MODULOS.items():
        if modulo in seleccionados and dependencia not in seleccionados:
            errores.append(f"Para activar {modulo.title()} debes activar Inventario.")
    if errores:
        raise ValidationError(errores)
    for codigo, _ in MODULOS_DISPONIBLES:
        ModuloNegocio.objects.update_or_create(
            negocio=negocio, modulo=codigo, defaults={"activo": codigo in seleccionados}
        )


def crear_modulos_por_defecto(negocio):
    for codigo, _ in MODULOS_DISPONIBLES:
        ModuloNegocio.objects.get_or_create(negocio=negocio, modulo=codigo, defaults={"activo": True})
