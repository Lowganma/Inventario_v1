from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from usuarios.models import Negocio


class Categoria(models.Model):
    negocio = models.ForeignKey(
        Negocio,
        on_delete=models.CASCADE,
        related_name="categorias_producto",
    )
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True)
    color = models.CharField(max_length=7, default="#0d6efd")
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["negocio", "nombre"],
                name="categoria_nombre_unico_por_negocio",
            ),
        ]

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    negocio = models.ForeignKey(
        Negocio,
        on_delete=models.CASCADE,
        related_name="productos",
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="productos",
    )
    codigo = models.CharField(max_length=100, blank=True)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True)
    stock = models.PositiveIntegerField(default=0)
    stock_minimo = models.PositiveIntegerField(default=0)
    costo = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    precio_venta = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nombre"]
        constraints = [
            # Los códigos vacíos pueden repetirse; un código informado es único
            # dentro del negocio al que pertenece el producto.
            models.UniqueConstraint(
                fields=["negocio", "codigo"],
                condition=~models.Q(codigo=""),
                name="producto_codigo_unico_por_negocio",
            ),
            models.CheckConstraint(
                check=models.Q(stock__gte=0),
                name="producto_stock_no_negativo",
            ),
            models.CheckConstraint(
                check=models.Q(stock_minimo__gte=0),
                name="producto_stock_minimo_no_negativo",
            ),
            models.CheckConstraint(
                check=models.Q(costo__gte=0),
                name="producto_costo_no_negativo",
            ),
            models.CheckConstraint(
                check=models.Q(precio_venta__gte=0),
                name="producto_precio_no_negativo",
            ),
        ]

    def clean(self):
        super().clean()
        # Impide asociar mediante código una categoría de otra empresa.
        if self.categoria_id and self.negocio_id:
            if self.categoria.negocio_id != self.negocio_id:
                raise ValidationError(
                    {"categoria": "La categoría debe pertenecer al mismo negocio."}
                )

    @property
    def stock_bajo(self):
        """Indica si las existencias alcanzaron el mínimo configurado."""
        return self.stock <= self.stock_minimo

    @property
    def valor_inventario(self):
        """Calcula el costo estimado de las existencias actuales."""
        return self.stock * self.costo

    def __str__(self):
        return self.nombre
