from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from usuarios.models import Negocio

from .models import CajaDiaria
from .services.caja import abrir_caja, cerrar_caja, obtener_resumen_caja, registrar_movimiento


class CajaDiariaServiceTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user("dueno", password="clave-segura")
        self.negocio = Negocio.objects.create(propietario=self.usuario, nombre="Uno")
        self.caja = abrir_caja(negocio=self.negocio, usuario=self.usuario, saldo_inicial=Decimal("50"))

    def test_abrir_y_no_duplicar_caja(self):
        self.assertEqual(self.caja.estado, "abierta")
        with self.assertRaises(ValidationError):
            abrir_caja(negocio=self.negocio, usuario=self.usuario, saldo_inicial=0)

    def test_movimientos_resumen_cierre_y_segundo_cierre(self):
        registrar_movimiento(negocio=self.negocio, usuario=self.usuario, tipo="ingreso", monto=100, metodo_pago="efectivo", concepto="Venta", origen="venta")
        registrar_movimiento(negocio=self.negocio, usuario=self.usuario, tipo="egreso", monto=20, metodo_pago="transferencia", concepto="Compra", origen="compra")
        self.assertEqual(obtener_resumen_caja(self.caja)["saldo_final_sistema"], Decimal("130"))
        cerrada = cerrar_caja(caja=self.caja, usuario=self.usuario, saldo_final_declarado=128)
        self.assertEqual(cerrada.diferencia, Decimal("-2"))
        with self.assertRaises(ValidationError):
            cerrar_caja(caja=cerrada, usuario=self.usuario, saldo_final_declarado=128)
        with self.assertRaises(ValidationError):
            registrar_movimiento(negocio=self.negocio, usuario=self.usuario, tipo="ingreso", monto=1, metodo_pago="efectivo", concepto="Tardío")

    def test_aislamiento_por_negocio(self):
        otro_usuario = User.objects.create_user("otro")
        otro = Negocio.objects.create(propietario=otro_usuario, nombre="Dos")
        abrir_caja(negocio=otro, usuario=otro_usuario, saldo_inicial=999)
        self.assertEqual(CajaDiaria.objects.filter(negocio=self.negocio).count(), 1)
        self.assertNotEqual(obtener_resumen_caja(self.caja)["saldo_final_sistema"], Decimal("999"))
