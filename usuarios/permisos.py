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


def usuario_es_dueno(usuario):
    """
    Indica si el usuario autenticado es el propietario
    del negocio actual.
    """

    if not usuario.is_authenticated:
        return False

    try:
        negocio = obtener_negocio(usuario)
    except PermissionDenied:
        return False

    return negocio.propietario_id == usuario.id

def dueno_required(vista):
    @wraps(vista)
    def protegida(request, *args, **kwargs):

        if not usuario_es_dueno(request.user):
            raise PermissionDenied(
                "Esta función está reservada para el dueño del negocio."
            )

        return vista(
            request,
            *args,
            **kwargs,
        )

    return protegida

def modulo_esta_activo(negocio, modulo):
    return ModuloNegocio.objects.filter(negocio=negocio, modulo=modulo, activo=True).exists()


def dueno_required(vista):
    @wraps(vista)
    def protegida(request, *args, **kwargs):
        if not usuario_es_dueno(request.user):
            raise PermissionDenied("Esta función está reservada para administradores.")
        return vista(request, *args, **kwargs)
    return protegida

usuario_es_admin = usuario_es_dueno
admin_required = dueno_required