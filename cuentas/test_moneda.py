from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from productos.models import Categoria, Producto
from usuarios.models import Negocio

from .models import TasaCambio


class MonedaDeConsultaTests(TestCase):
    def setUp(self):
        usuario = get_user_model().objects.create_user("comercio")
        negocio = Negocio.objects.create(propietario=usuario, nombre="Papelería")
        categoria = Categoria.objects.create(negocio=negocio, nombre="Escolar")
        Producto.objects.create(
            negocio=negocio, categoria=categoria, nombre="Lápiz",
            precio_venta=Decimal("2.50"), stock=10,
        )
        self.client.force_login(usuario)

    def test_selector_global_con_la_precision_completa_de_la_tasa(self):
        TasaCambio.objects.create(moneda="USD", valor=Decimal("50.251234"), fecha_vigencia=date.today())
        for ruta in ("inicio", "productos:index", "caja:dashboard", "ventas:lista",
                     "compras:lista", "cuentas:lista", "clientes:lista"):
            with self.subTest(ruta=ruta):
                respuesta = self.client.get(reverse(ruta))
                self.assertContains(respuesta, 'data-moneda-vista="bs"')
                self.assertContains(respuesta, 'data-tasa="50.251234"')

    def test_inventario_filtrado_conserva_los_dolares_convertibles_incluso_sin_tasa(self):
        respuesta = self.client.get(
            reverse("productos:index"), {"buscar": "Lápiz"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertContains(respuesta, 'class="ot-importe" value="2.50"')
        self.assertContains(self.client.get(reverse("inicio")), 'data-tasa="0"')
