from django.contrib.auth.models import User
from django.db import models


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