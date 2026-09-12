from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from clientes.models import Cliente
from cuentas.models import CuentaPorCobrar
from productos.models import Producto, PresentacionProducto
from usuarios.models import Negocio


class Venta(models.Model):
    TIPOS_PAGO = [
        ("contado", "Pago inmediato"),
        ("fiado", "Fiado"),
    ]

    ESTADOS = [
        ("completada", "Completada"),
        ("anulada", "Anulada"),
    ]

    METODOS_PAGO = [
        ("efectivo", "Efectivo"),
        ("transferencia", "Transferencia"),
        ("divisa", "Divisa"),
        ("otro", "Otro"),
    ]

    TIPOS_DESCUENTO = [
        ("porcentaje", "Porcentaje"),
        ("fijo", "Monto fijo"),
    ]

    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE, related_name="ventas")
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
    fecha = models.DateTimeField(auto_now_add=True)

    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    descuento = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    tipo_descuento = models.CharField(
        max_length=20,
        choices=TIPOS_DESCUENTO,
        blank=True,
    )
    valor_descuento = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    tipo_pago = models.CharField(max_length=20, choices=TIPOS_PAGO, default="contado")
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO, blank=True)
    referencia_pago = models.CharField(max_length=100, blank=True)
    detalle_pago = models.CharField(max_length=255, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default="completada")
    notas = models.TextField(blank=True)
    numero = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-fecha", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["negocio", "numero"],
                name="venta_numero_unico_por_negocio",
            ),
        ]

    def __str__(self):
        return f"Venta #{self.numero or self.pk}"


class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="detalles")
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name="detalles_venta",
    )
    presentacion = models.ForeignKey(
        PresentacionProducto,
        on_delete=models.PROTECT,
        related_name="detalles_venta",
        null=True,
        blank=True,
    )
    cantidad = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    factor_presentacion = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("1.00"),
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    precio_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    costo_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    def calcular_subtotal(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        if self.presentacion:
            return f"{self.presentacion.nombre} x {self.cantidad}"
        return f"{self.producto.nombre} x {self.cantidad}"
