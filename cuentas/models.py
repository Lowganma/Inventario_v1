from django.db import models

from clientes.models import Cliente


class CuentaPorCobrar(models.Model):
    ESTADOS = [
        ("pendiente", "Pendiente"),
        ("pagada", "Pagada"),
    ]

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name="cuentas",
    )

    concepto = models.CharField(max_length=150)

    monto_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    fecha = models.DateTimeField(
    auto_now_add=True,
    verbose_name="Fecha y hora de creación",
)

    fecha_vencimiento = models.DateField(
        blank=True,
        null=True,
    )

    estado = models.CharField(
        max_length=10,
        choices=ESTADOS,
        default="pendiente",
    )

    notas = models.TextField(blank=True)

    @property
    def total_abonado(self):
         return sum(
            abono.monto_pagado
            for abono in self.abonos.all()
        )


    @property
    def saldo_pendiente(self):
        return self.monto_total - self.total_abonado

    def __str__(self):
        return f"{self.cliente} - {self.concepto}"


class Abono(models.Model):
    METODOS_PAGO = [
        ("efectivo", "Efectivo"),
        ("transferencia", "Transferencia"),
        ("divisa", "Divisa"),
        ("otro", "Otro"),
    ]

    cuenta = models.ForeignKey(
        CuentaPorCobrar,
        on_delete=models.CASCADE,
        related_name="abonos",
    )

    monto_pagado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    fecha_pago = models.DateField()

    metodo = models.CharField(
        max_length=20,
        choices=METODOS_PAGO,
    )

    referencia = models.CharField(
        max_length=100,
        blank=True,
    )

    notas = models.TextField(blank=True)

    def __str__(self):
        return f"{self.cuenta.cliente} - {self.monto_pagado}"