from django.contrib.auth.models import User
from django.db import models


MODULOS_DISPONIBLES = [
    ("clientes", "Clientes"),
    ("cuentas", "Cuentas por cobrar"),
    ("inventario", "Inventario"),
    ("compras", "Compras"),
    ("ventas", "Ventas"),
    ("caja", "Caja"),
]


class Negocio(models.Model):
    """
    Representa el negocio asociado a un usuario propietario.

    En esta primera versión:
    un usuario solo puede tener un negocio.
    """

    propietario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="negocio",
    )

    nombre = models.CharField(
        max_length=150,
    )

    telefono = models.CharField(
        max_length=20,
        blank=True,
    )

    fecha_registro = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return self.nombre


class PerfilUsuario(models.Model):
    """Vincula empleados con un negocio y define su rol RBAC."""

    ROLES = [("admin", "Administrador"), ("empleado", "Empleado")]
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil_negocio")
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE, related_name="miembros")
    rol = models.CharField(max_length=10, choices=ROLES, default="empleado")

    def __str__(self):
        return f"{self.usuario.username} - {self.get_rol_display()}"


class ModuloNegocio(models.Model):
    """Configuración escalable de funcionalidades habilitadas por negocio."""

    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE, related_name="modulos")
    modulo = models.CharField(max_length=30, choices=MODULOS_DISPONIBLES)
    activo = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["negocio", "modulo"], name="modulo_unico_por_negocio")
        ]

    def __str__(self):
        return f"{self.negocio} - {self.get_modulo_display()}"
