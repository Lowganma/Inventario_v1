from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
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

    color = models.CharField(
        max_length=7,
        default="#0d6efd",
        validators=[
            RegexValidator(
                regex=r"^#[0-9A-Fa-f]{6}$",
                message=(
                    "Introduce un color hexadecimal válido "
                    "(por ejemplo, #0d6efd)."
                ),
            )
        ],
    )

    activa = models.BooleanField(default=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["negocio", "nombre"],
                name="categoria_nombre_unico_por_negocio",
            ),
            models.UniqueConstraint(
            fields=["negocio", "nombre"],
            name="producto_nombre_unico_por_negocio",
        ),

        ]

    def __str__(self):
        return self.nombre


class Producto(models.Model):

    # =========================================================
    # OPCIONES
    # =========================================================

    TIPOS = [
        ("producto", "Producto físico"),
        ("servicio", "Servicio"),
    ]

    UNIDADES = [
        ("unidad", "Unidad"),
        ("hoja", "Hoja"),
        ("kg", "Kilogramo"),
        ("g", "Gramo"),
        ("litro", "Litro"),
        ("ml", "Mililitro"),
        ("metro", "Metro"),
    ]

    # =========================================================
    # RELACIONES
    # =========================================================

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

    # =========================================================
    # DATOS GENERALES
    # =========================================================

    tipo = models.CharField(
        max_length=20,
        choices=TIPOS,
        default="producto",
    )

    unidad_base = models.CharField(
        max_length=20,
        choices=UNIDADES,
        default="unidad",
    )

    codigo = models.CharField(
        max_length=100,
        blank=True,
    )

    nombre = models.CharField(
        max_length=255,
    )

    descripcion = models.TextField(
        blank=True,
    )

    # =========================================================
    # INVENTARIO
    # =========================================================

    stock = models.DecimalField(
        max_digits=14,
        decimal_places=3,
        default=Decimal("0.000"),
        validators=[
            MinValueValidator(Decimal("0.000")),
        ],
    )

    stock_minimo = models.DecimalField(
        max_digits=14,
        decimal_places=3,
        default=Decimal("0.000"),
        validators=[
            MinValueValidator(Decimal("0.000")),
        ],
    )

    # =========================================================
    # PRECIOS
    # =========================================================

    costo = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00")),
        ],
    )

    precio_venta = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00")),
        ],
    )

    # =========================================================
    # ESTADO Y FECHAS
    # =========================================================

    activo = models.BooleanField(default=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    fecha_actualizacion = models.DateTimeField(auto_now=True)

    # =========================================================
    # META
    # =========================================================

    class Meta:
        ordering = ["nombre"]

        constraints = [
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

    # =========================================================
    # VALIDACIONES
    # =========================================================

    def clean(self):
        super().clean()

        # -----------------------------------------------------
        # Categoría del mismo negocio
        # -----------------------------------------------------

        if self.categoria_id and self.negocio_id:
            if self.categoria.negocio_id != self.negocio_id:
                raise ValidationError(
                    {
                        "categoria":
                            "La categoría debe pertenecer "
                            "al mismo negocio."
                    }
                )

        # -----------------------------------------------------
        # Unidades que deben ser enteras
        # -----------------------------------------------------

        unidades_enteras = {
            "unidad",
            "hoja",
        }

        if self.unidad_base in unidades_enteras:

            if (
                self.stock is not None
                and self.stock != self.stock.to_integral_value()
            ):
                raise ValidationError(
                    {
                        "stock":
                            "El stock debe ser un número entero "
                            "para esta unidad."
                    }
                )

            if (
                self.stock_minimo is not None
                and self.stock_minimo
                != self.stock_minimo.to_integral_value()
            ):
                raise ValidationError(
                    {
                        "stock_minimo":
                            "El stock mínimo debe ser un número "
                            "entero para esta unidad."
                    }
                )

        # -----------------------------------------------------
        # Precio de venta
        # -----------------------------------------------------

        if (
            self.costo is not None
            and self.precio_venta is not None
            and self.precio_venta < self.costo
        ):
            raise ValidationError(
                {
                    "precio_venta":
                        "El precio de venta no puede ser "
                        "menor que el costo."
                }
            )

    # =========================================================
    # PROPIEDADES DE INVENTARIO
    # =========================================================

    @property
    def stock_bajo(self):
        """Indica si las existencias alcanzaron el mínimo."""
        return self.stock <= self.stock_minimo

    @property
    def valor_inventario(self):
        """Costo estimado de las existencias actuales."""
        return self.stock * self.costo

    # =========================================================
    # FORMATO DE UNIDADES
    # =========================================================

    def _formatear_cantidad(self, cantidad):
        """
        Muestra enteros sin decimales y cantidades fraccionarias
        sin ceros innecesarios.
        """

        unidades_enteras = {
            "unidad",
            "hoja",
        }

        if self.unidad_base in unidades_enteras:
            return str(int(cantidad))

        return format(cantidad.normalize(), "f")

    def _nombre_unidad(self, cantidad):
        """
        Devuelve una unidad legible y aplica singular/plural
        cuando corresponde.
        """

        unidades = {
            "unidad": ("unidad", "unidades"),
            "hoja": ("hoja", "hojas"),
            "kg": ("kg", "kg"),
            "g": ("g", "g"),
            "litro": ("L", "L"),
            "ml": ("ml", "ml"),
            "metro": ("m", "m"),
        }

        singular, plural = unidades.get(
            self.unidad_base,
            (
                self.get_unidad_base_display(),
                self.get_unidad_base_display(),
            ),
        )

        if cantidad == 1:
            return singular

        return plural

    @property
    def stock_con_unidad(self):
        cantidad = self._formatear_cantidad(self.stock)
        unidad = self._nombre_unidad(self.stock)

        return f"{cantidad} {unidad}"

    @property
    def stock_minimo_con_unidad(self):
        cantidad = self._formatear_cantidad(
            self.stock_minimo
        )

        unidad = self._nombre_unidad(
            self.stock_minimo
        )

        return f"{cantidad} {unidad}"

    # =========================================================
    # REPRESENTACIÓN
    # =========================================================

    def __str__(self):
        return self.nombre