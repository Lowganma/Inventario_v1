from .models import MODULOS_DISPONIBLES
from .permisos import obtener_negocio, usuario_es_admin


def configuracion_negocio(request):
    """Expone módulos y rol una sola vez para toda la navegación."""
    activos = {codigo: False for codigo, _ in MODULOS_DISPONIBLES}
    if request.user.is_authenticated:
        negocio = obtener_negocio(request.user)
        activos.update({fila.modulo: fila.activo for fila in negocio.modulos.all()})
    return {"modulos_activos": activos, "usuario_es_admin": usuario_es_admin(request.user)}
