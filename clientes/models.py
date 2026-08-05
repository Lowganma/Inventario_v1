from django.db import models
from usuarios.models import Negocio

# Create your models here.
class Cliente(models.Model):
    Estados = [
        ('Activo', 'Activo'),
        ('Suspendido', 'Suspendido'),
    ]

    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)
    estado = models.CharField(
        max_length=10,
        choices=Estados,
        default='Activo',
    )
    
    fecha_registro = models.DateTimeField(auto_now_add=True)

    negocio = models.ForeignKey(
        Negocio,
        on_delete=models.CASCADE,
        related_name='clientes',
    )

    def __str__(self):
        return self.nombre


class Pago(models.Model):
    METODOS_PAGO = [
        ('Efectivo', 'Efectivo'),
        ('Transferencia', 'Transferencia'),
        ('Divisa', 'Divisa'),
        ("otro", "otro"),
    ]

    cliente = models.ForeignKey(
        Cliente, on_delete=models.CASCADE,
        related_name='pagos'
    )
    monto_pagado = models.DecimalField(max_digits=8, decimal_places=2)
    fecha_pago = models.DateField()
    metodo = models.CharField(
        max_length=20,
        choices=METODOS_PAGO,
    )
    referencia = models.CharField(max_length=100, blank=True)
    notas = models.TextField(blank=True)

    def __str__(self):
        return f"{self.cliente.nombre} - {self.monto_pagado}"
    