from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from clientes.models import Cliente
from usuarios.models import Negocio
from .models import CuentaPorCobrar


class CuentaSecurityTests(TestCase):
    def test_cannot_access_or_pay_another_business_account(self):
        owner = User.objects.create_user("owner", password="test-password-123")
        other = User.objects.create_user("other", password="test-password-123")
        Negocio.objects.create(propietario=owner, nombre="Uno")
        other_business = Negocio.objects.create(propietario=other, nombre="Dos")
        customer = Cliente.objects.create(
            nombre="Ajeno", apellido="Dos", telefono="2", negocio=other_business
        )
        account = CuentaPorCobrar.objects.create(
            cliente=customer, concepto="Secreto", monto_total=Decimal("20.00")
        )
        self.client.force_login(owner)

        routes = ("cuentas:detalle", "cuentas:registrar_abono", "cuentas:pagar_completo")
        for route in routes:
            response = self.client.get(reverse(route, args=[account.id]))
            self.assertEqual(response.status_code, 404)
