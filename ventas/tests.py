from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from caja.services.caja import abrir_caja
from clientes.models import Cliente
from productos.models import Categoria, Producto
from usuarios.models import Negocio
from .models import Venta


class ComprobanteVentaTests(TestCase):
    def setUp(self):
        user = User.objects.create_user("papeleria")
        negocio = Negocio.objects.create(nombre="Papelería", propietario=user)
        abrir_caja(negocio=negocio, usuario=user, saldo_inicial=0)
        self.cliente = Cliente.objects.create(negocio=negocio, nombre="Ana")
        categoria = Categoria.objects.create(negocio=negocio, nombre="Escolar")
        self.producto = Producto.objects.create(
            negocio=negocio, categoria=categoria, nombre="Cuaderno", stock=9, precio_venta=3,
        )
        self.client.force_login(user)

    def guardar(self, tipo_pago, precio):
        return self.client.post(reverse("ventas:crear"), {
            "tipo_pago": tipo_pago, "cliente": self.cliente.pk,
            "metodo_pago": "efectivo" if tipo_pago == "contado" else "",
            "form-TOTAL_FORMS": "1", "form-INITIAL_FORMS": "0",
            "form-0-producto": self.producto.pk, "form-0-cantidad": "2",
            "form-0-precio_unitario": precio,
        }, follow=True)

    def test_fiado_con_precio_editado_abre_el_comprobante_y_crea_la_deuda(self):
        respuesta = self.guardar("fiado", "2.25")
        venta = Venta.objects.get()
        self.assertRedirects(respuesta, reverse("ventas:detalle", args=[venta.pk]))
        self.assertContains(respuesta, "Fiado")
        self.assertEqual(venta.total, Decimal("4.50"))
        self.assertEqual(venta.cuenta_por_cobrar.saldo_pendiente, venta.total)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 7)
        self.assertEqual(self.producto.precio_venta, 3)

    def test_contado_sin_precio_editado_usa_el_precio_del_catalogo(self):
        respuesta = self.guardar("contado", "")
        venta = Venta.objects.get()
        self.assertRedirects(respuesta, reverse("ventas:detalle", args=[venta.pk]))
        self.assertContains(respuesta, "Pago inmediato")
        self.assertEqual(venta.total, 6)
        self.assertIsNone(venta.cuenta_por_cobrar_id)
