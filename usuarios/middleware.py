from .models import Negocio


class EnsureNegocioMiddleware:
    """Garantiza que todo usuario autenticado tenga un ámbito de datos."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not hasattr(request.user, "negocio"):
            negocio, _ = Negocio.objects.get_or_create(
                propietario=request.user,
                defaults={"nombre": f"Negocio de {request.user.username}"},
            )
            # Evita conservar en la instancia el resultado negativo que dejó
            # la primera consulta al descriptor OneToOne.
            request.user.negocio = negocio

        return self.get_response(request)
