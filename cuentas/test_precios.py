from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from bs4 import BeautifulSoup

from django.contrib.auth.models import User
from django.template import Context, Template
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils.translation import override

from clientes.models import Cliente
from productos.models import Categoria, Producto
from usuarios.models import Negocio
from ventas.models import DetalleVenta, Venta
from .models import CuentaPorCobrar, TasaCambio
from caja.models import CajaDiaria, MovimientoCaja
from django.utils import timezone


class PrecioDobleTests(SimpleTestCase):
    def test_un_solo_importe_visible_incluso_sin_css_ni_javascript(self):
        for tasa in [None, SimpleNamespace(valor=Decimal('887.3'), fecha_vigencia=date.today())]:
            with self.subTest(tasa=tasa):
                html = BeautifulSoup(self.render_precio(Decimal('0.40'), tasa), 'html.parser')
                self.assertEqual(html.get_text(), '$0.40')
                self.assertEqual(html.span['data-importe-usd'], '0.40')
                self.assertEqual(len(html.select('[data-importe-usd]')), 1)

    def render_precio(self, valor, tasa=None):
        return Template('{% load precios %}{% precio_moneda valor %}').render(
            Context({'valor': valor, 'tasa_bcv_global': tasa})
        )

    def test_conversion_y_redondeo_decimal(self):
        tasa = SimpleNamespace(valor=Decimal('887.3'), fecha_vigencia=date(2026, 10, 27))
        html = self.render_precio(Decimal('0.40'), tasa)
        self.assertIn('$0.40', html)
        self.assertIn('Bs. 354,92', html)
        self.assertIn('27/10/2026', html)

    def test_redondea_medio_centimo_hacia_arriba(self):
        tasa = SimpleNamespace(valor=Decimal('10.05'), fecha_vigencia=date.today())
        self.assertIn('Bs. 1,01', self.render_precio(Decimal('0.10'), tasa))

    def test_cero_y_negativos(self):
        tasa = SimpleNamespace(valor=Decimal('100'), fecha_vigencia=date.today())
        self.assertIn('Bs. 0,00', self.render_precio(0, tasa))
        self.assertIn('Bs. -125,00', self.render_precio(Decimal('-1.25'), tasa))

    def test_sin_tasa_o_tasa_no_valida_no_inventa_conversion(self):
        for valor in [None, '0', '-1', 'NaN']:
            tasa = SimpleNamespace(valor=valor, fecha_vigencia=date.today()) if valor else None
            html = self.render_precio(Decimal('10'), tasa)
            self.assertIn('$10.00', html)
            self.assertIn('Tasa BCV no disponible', html)
            self.assertNotIn('Bs. 0,00', html)


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class PrecioDoblePaginasTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = User.objects.create_user('precios')
        cls.negocio = Negocio.objects.create(propietario=cls.usuario, nombre='Tienda')
        cls.categoria = Categoria.objects.create(negocio=cls.negocio, nombre='Servicios')
        cls.producto = Producto.objects.create(
            negocio=cls.negocio, categoria=cls.categoria, nombre='Copia',
            tipo='servicio', precio_venta=Decimal('0.40'), costo=Decimal('0.10'),
        )
        cls.cliente = Cliente.objects.create(negocio=cls.negocio, nombre='Ana', apellido='Uno', telefono='1')
        cls.cuenta = CuentaPorCobrar.objects.create(cliente=cls.cliente, concepto='Copias', monto_total=Decimal('0.40'))
        cls.venta = Venta.objects.create(negocio=cls.negocio, usuario=cls.usuario, total=Decimal('0.40'))
        DetalleVenta.objects.create(venta=cls.venta, producto=cls.producto, cantidad=1, precio_unitario=Decimal('0.40'), costo_unitario=Decimal('0.10'), subtotal=Decimal('0.40'))
        cls.caja = CajaDiaria.objects.create(negocio=cls.negocio, abierta_por=cls.usuario, fecha=timezone.localdate(), saldo_inicial=Decimal('0.40'))
        MovimientoCaja.objects.create(negocio=cls.negocio, usuario=cls.usuario, tipo='ingreso', monto=Decimal('0.40'), metodo_pago='efectivo', concepto='Prueba')
        TasaCambio.objects.create(valor=Decimal('800'), fecha_vigencia=date(2026, 10, 26))
        TasaCambio.objects.create(valor=Decimal('887.3'), fecha_vigencia=date(2026, 10, 27))

    def setUp(self):
        self.client.force_login(self.usuario)

    def test_caja_productos_y_catalogo_comparten_el_mismo_selector(self):
        for nombre in ['productos:index', 'caja:dashboard', 'ventas:crear']:
            with self.subTest(vista=nombre):
                response = self.client.get(reverse(nombre))
                html = BeautifulSoup(response.content, 'html.parser')
                controles = html.select('.catalogo-view-toggle.moneda-selector')
                self.assertEqual(len(controles), 1)
                self.assertEqual([b.get_text() for b in controles[0].select('button')], ['$', 'Bs'])
                self.assertEqual(controles[0].select_one('.active')['data-moneda'], 'usd')
                self.assertNotIn('moneda-toolbar', str(html))

    def test_listas_y_detalles_incluyen_importes_para_el_selector(self):
        rutas = [
            reverse('productos:index'), reverse('productos:detalle', args=[self.producto.pk]),
            reverse('cuentas:lista'), reverse('cuentas:detalle', args=[self.cuenta.pk]),
            reverse('ventas:lista'), reverse('ventas:detalle', args=[self.venta.pk]),
            reverse('ventas:crear'), reverse('inicio'),
            reverse('caja:dashboard'), reverse('caja:movimientos'), reverse('caja:cierres'),
            reverse('caja:detalle_cierre', args=[self.caja.pk]),
            reverse('cuentas:registrar_abono', args=[self.cuenta.pk]),
            reverse('cuentas:pagar_completo', args=[self.cuenta.pk]),
        ]
        for url in rutas:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(response, 'data-moneda="bs"')
                self.assertContains(response, '$0.40')
                self.assertContains(response, 'Bs. 354,92')

    def test_lista_ajax_y_localizacion_espanola(self):
        with override('es'):
            response = self.client.get(reverse('productos:index'), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertContains(response, 'Bs. 354,92')
            response = self.client.get(reverse('ventas:crear'))
            self.assertContains(response, 'data-tasa="887.300000"')
            self.assertContains(response, 'data-precio-usd="0.40"')

    def test_pagina_sin_tasa(self):
        TasaCambio.objects.all().delete()
        response = self.client.get(reverse('productos:index'))
        self.assertContains(response, 'Tasa BCV no disponible')
        self.assertContains(response, '$0.40')

    def test_selector_bloquea_bolivares_sin_tasa(self):
        TasaCambio.objects.all().delete()
        response = self.client.get(reverse('productos:index'))
        self.assertContains(response, 'disabled title="Actualiza la tasa BCV')

    def test_cierre_muestra_el_saldo_completo_en_la_moneda_seleccionable(self):
        response = self.client.get(reverse('caja:cerrar'))
        self.assertContains(response, '$0.80')
        self.assertContains(response, 'Bs. 709,84')
