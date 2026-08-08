from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'usuarios'

    def ready(self):
        # Registra la inicialización modular de negocios recién creados.
        from . import signals  # noqa: F401
