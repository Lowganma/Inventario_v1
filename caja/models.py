from django.db import models

# Create your models here.
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from usuarios.models import Negocio


class CajaDiaria(models.Model):
    """Jornada financiera; los movimientos se relacionan por negocio y fecha."""

    ESTADOS = [("abierta", "Abierta"), ("cerrada", "Cerrada")]
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE, related_name="cajas_diarias")
    fecha = models.DateField()
    estado = models.CharField(max_length=10, choices=ESTADOS, default="abierta")
    saldo_inicial = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    saldo_final_sistema = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    saldo_final_declarado = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    diferencia = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    fecha_apertura = models.DateTimeField(auto_now_add=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    abierta_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="cajas_abiertas")
    cerrada_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="cajas_cerradas", null=True, blank=True)
    notas = models.TextField(blank=True)

    class Meta:
        ordering = ["-fecha", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["negocio", "fecha"], name="caja_unica_por_negocio_fecha")
        ]

    def __str__(self):
        return f"Caja {self.fecha:%d/%m/%Y} - {self.negocio}"


class MovimientoCaja(models.Model):
    """
    Representa una entrada o salida real de dinero del negocio.

    Caja no sustituye a los módulos comerciales. Conserva
    exclusivamente el efecto financiero de operaciones como
    ventas, abonos, compras y movimientos manuales.
    """

    TIPOS = [
        ("ingreso", "Ingreso"),
        ("egreso", "Egreso"),
    ]

    ORIGENES = [
        ("venta", "Venta"),
        ("abono", "Abono"),
        ("compra", "Compra"),
        ("manual", "Movimiento manual"),
    ]

    METODOS_PAGO = [
        ("efectivo", "Efectivo"),
        ("transferencia", "Transferencia"),
        ("divisa", "Divisa"),
        ("otro", "Otro"),
    ]

    negocio = models.ForeignKey(
        Negocio,
        on_delete=models.CASCADE,
        related_name="movimientos_caja",
    )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="movimientos_caja_registrados",
    )

    tipo = models.CharField(
        max_length=10,
        choices=TIPOS,
    )

    origen = models.CharField(
        max_length=20,
        choices=ORIGENES,
        default="manual",
    )

    monto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.01")),
        ],
    )

    metodo_pago = models.CharField(
        max_length=20,
        choices=METODOS_PAGO,
    )

    concepto = models.CharField(
        max_length=180,
    )

    referencia = models.CharField(
        max_length=100,
        blank=True,
    )

    notas = models.TextField(
        blank=True,
    )

    fecha = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = [
            "-fecha",
            "-id",
        ]

    def __str__(self):
        return (
            f"{self.get_tipo_display()} - "
            f"{self.concepto} - "
            f"${self.monto}"
        )
