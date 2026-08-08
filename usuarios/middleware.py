from django.core.exceptions import PermissionDenied

from .models import Negocio
from .permisos import modulo_esta_activo, obtener_negocio


class EnsureNegocioMiddleware:
    """Garantiza que todo usuario autenticado tenga un ámbito de datos."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                negocio = obtener_negocio(request.user)
            except PermissionDenied:
                negocio, _ = Negocio.objects.get_or_create(
                    propietario=request.user,
                    defaults={"nombre": f"Negocio de {request.user.username}"},
                )
            # Evita conservar en la instancia el resultado negativo que dejó
            # el descriptor OneToOne y conserva compatibilidad con las apps.
            # Inyectamos la caché del descriptor sin reasignar el propietario
            # real del objeto Negocio cuando quien inicia sesión es empleado.
            request.user._state.fields_cache["negocio"] = negocio
            request.negocio = negocio

        return self.get_response(request)


class ModuleAccessMiddleware:
    """Impide el acceso por URL a apps desactivadas, no solo oculta enlaces."""

    NAMESPACE_MODULO = {
        "clientes": "clientes", "cuentas": "cuentas", "productos": "inventario",
        "compras": "compras", "ventas": "ventas", "caja": "caja",
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not request.user.is_authenticated:
            return None
        namespace = getattr(request.resolver_match, "namespace", "")
        modulo = self.NAMESPACE_MODULO.get(namespace)
        if modulo and not modulo_esta_activo(request.negocio, modulo):
            raise PermissionDenied("Este módulo no está activo para el negocio.")
        return None
