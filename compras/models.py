from django.db import models
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator

from usuarios.models import Negocio
from productos.models import Producto

# Create your models here.

class Compra(models.Model):
    """

    Registra una operacion de reposicion de inventario.

    La compra pertenece siempre al negocio del usuario 
    que la registra y puede contener uno o varios productos.
    """

    negocio = models.ForeignKey(
        Negocio,
        on_delete=models.CASCADE,
        related_name="compras",
    )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="compras_registradas",
    )

    fecha = models.DateField(
        auto_now_add=True,
    )

    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00")),
                    ],
    )

    notas = models.TextField(
        blank=True,
    )

    class Meta:
        ordering = [
            "-fecha",
            "-id",
        ]

    verbose_name = "compra"
    verbose_name_plural = "compras"

    def __str__(self):
        return f"Compra #{self.pk}"



class DetalleCompra(models.Model):
    """
    Guarda cada producto incluido en una compra.

    El precio de cada compra queda registrado historicamente,
    aunque posteriormente cambie el costo vigente del producto.
    """

    compra = models.ForeignKey(
        Compra,
        on_delete=models.CASCADE,
        related_name="detalles",
    )

    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name="detalles_compra",
    )   

    cantidad = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
    )

    precio_compra = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00")),
                    ],
    )

    precio_venta = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00")),
                    ],
    )

    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    def calcular_subtotal(self):
        """
        Calcula el costo total correspondiente a esta linea
        """
        return self.precio_compra * self.cantidad

    def __str__(self):
        return (
            f"{self.producto.nombre} - "
            f"{self.cantidad} "
        )
