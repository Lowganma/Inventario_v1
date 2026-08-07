from django.db import models

# Create your models here.
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from clientes.models import Cliente
from productos.models import Producto
from usuarios.models import Negocio
from cuentas.models import CuentaPorCobrar

class Venta(models.Model):
    """
    Representa una operación de venta realizada por un negocio.

    Una venta puede ser pagada inmediatamente o quedar
    asociada posteriormente a una cuenta por cobrar.
    """

    TIPOS_PAGO = [
        ("contado", "Pago inmediato"),
        ("fiado", "Fiado"),
    ]

    ESTADOS = [
        ("completada", "Completada"),
        ("anulada", "Anulada"),
    ]

    negocio = models.ForeignKey(
        Negocio,
        on_delete=models.CASCADE,
        related_name="ventas",
    )

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name="ventas",
        null=True,
        blank=True,
    )

    cuenta_por_cobrar = models.OneToOneField(
    CuentaPorCobrar,
    on_delete=models.SET_NULL,
    related_name="venta",
    null=True,
    blank=True,
    )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="ventas_registradas",
    )

    fecha = models.DateTimeField(
        auto_now_add=True,
    )

    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00")),
        ],
    )

    descuento = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00")),
        ],
    )

    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00")),
        ],
    )

    tipo_pago = models.CharField(
        max_length=20,
        choices=TIPOS_PAGO,
        default="contado",
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default="completada",
    )

    notas = models.TextField(
        blank=True,
    )

    class Meta:
        ordering = [
            "-fecha",
            "-id",
        ]

    def __str__(self):
        return f"Venta #{self.pk}"


class DetalleVenta(models.Model):
    """
    Guarda cada producto incluido dentro de una venta.

    Conserva el precio y costo del producto al momento
    de vender para mantener historial y permitir cálculos
    de utilidad posteriormente.
    """

    venta = models.ForeignKey(
        Venta,
        on_delete=models.CASCADE,
        related_name="detalles",
    )

    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name="detalles_venta",
    )

    cantidad = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
        ],
    )

    precio_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.00")),
        ],
    )

    costo_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.00")),
        ],
    )

    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    def calcular_subtotal(self):
        """
        Calcula el subtotal correspondiente a esta línea.
        """
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return (
            f"{self.producto.nombre} "
            f"x {self.cantidad}"
        )