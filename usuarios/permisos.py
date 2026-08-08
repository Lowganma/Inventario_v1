from functools import wraps

from django.core.exceptions import PermissionDenied

from .models import ModuloNegocio


def obtener_negocio(usuario):
    """Obtiene el ámbito empresarial tanto del propietario como de un miembro."""
    try:
        return usuario.negocio
    except (AttributeError, usuario._meta.model.DoesNotExist):
        try:
            return usuario.perfil_negocio.negocio
        except AttributeError as error:
            raise PermissionDenied("El usuario no pertenece a un negocio.") from error


def usuario_es_admin(usuario):
    if not usuario.is_authenticated:
        return False
    try:
        obtener_negocio(usuario)
    except PermissionDenied:
        return False
    negocio = obtener_negocio(usuario)
    if negocio.propietario_id == usuario.id:
        return True
    return getattr(getattr(usuario, "perfil_negocio", None), "rol", None) == "admin"


def modulo_esta_activo(negocio, modulo):
    return ModuloNegocio.objects.filter(negocio=negocio, modulo=modulo, activo=True).exists()


def admin_required(vista):
    @wraps(vista)
    def protegida(request, *args, **kwargs):
        if not usuario_es_admin(request.user):
            raise PermissionDenied("Esta función está reservada para administradores.")
        return vista(request, *args, **kwargs)
    return protegida
