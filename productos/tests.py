from decimal import Decimal

from django.contrib.auth.models import User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import Http404
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from usuarios.models import Negocio

from .models import Categoria, Producto
from . import views


@override_settings(
    STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage"
)
class InventarioMultiempresaTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user("uno", password="prueba-segura")
        self.otro_usuario = User.objects.create_user("dos", password="prueba-segura")
        self.negocio = Negocio.objects.create(propietario=self.usuario, nombre="Tienda Uno")
        self.otro_negocio = Negocio.objects.create(propietario=self.otro_usuario, nombre="Tienda Dos")
        self.categoria = Categoria.objects.create(negocio=self.negocio, nombre="Bebidas")
        self.otra_categoria = Categoria.objects.create(negocio=self.otro_negocio, nombre="Snacks")
        self.producto = self.crear_producto(self.negocio, self.categoria, "Refresco")
        self.otro_producto = self.crear_producto(self.otro_negocio, self.otra_categoria, "Papas")
        self.factory = RequestFactory()

    def request(self, method, url, data=None):
        request = getattr(self.factory, method)(url, data=data or {})
        request.user = self.usuario
        SessionMiddleware(lambda response: response).process_request(request)
        request.session.save()
        request._messages = FallbackStorage(request)
        return request

    @staticmethod
    def crear_producto(negocio, categoria, nombre, **campos):
        valores = {"stock": 10, "stock_minimo": 3, "costo": Decimal("1.20"), "precio_venta": Decimal("2.00")}
        valores.update(campos)
        return Producto.objects.create(negocio=negocio, categoria=categoria, nombre=nombre, **valores)

    def test_usuario_solo_ve_productos_de_su_negocio(self):
        respuesta = views.index(self.request("get", reverse("productos:index")))
        contenido = respuesta.content.decode()
        self.assertIn("Refresco", contenido)
        self.assertNotIn("Papas", contenido)

    def test_usuario_no_accede_a_producto_de_otro_negocio(self):
        with self.assertRaises(Http404):
            views.detalle(self.request("get", "/"), self.otro_producto.id)
        with self.assertRaises(Http404):
            views.editar_producto(self.request("get", "/"), self.otro_producto.id)

    def test_crear_producto_asigna_el_negocio_autenticado(self):
        respuesta = views.crear_producto(self.request("post", reverse("productos:crear"), {"categoria": self.categoria.id, "codigo": "B-01", "nombre": "Agua", "descripcion": "", "stock": 5, "stock_minimo": 1, "costo": "0.50", "precio_venta": "1.00", "activo": "on"}))
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(Producto.objects.get(nombre="Agua").negocio, self.negocio)

    def test_categorias_visibles_solo_pertenecen_al_negocio(self):
        respuesta = views.lista_categorias(self.request("get", reverse("productos:categorias")))
        contenido = respuesta.content.decode()
        self.assertIn("Bebidas", contenido)
        self.assertNotIn("Snacks", contenido)
        with self.assertRaises(Http404):
            views.editar_categoria(self.request("get", "/"), self.otra_categoria.id)

    def test_stock_bajo_incluye_igualdad_con_el_minimo(self):
        self.producto.stock = 3
        self.assertTrue(self.producto.stock_bajo)
        self.producto.stock = 4
        self.assertFalse(self.producto.stock_bajo)

    def test_valor_inventario(self):
        self.assertEqual(self.producto.valor_inventario, Decimal("12.00"))

    def test_no_permite_categoria_de_otro_negocio_al_crear(self):
        respuesta = views.crear_producto(self.request("post", reverse("productos:crear"), {"categoria": self.otra_categoria.id, "nombre": "Intruso", "stock": 0, "stock_minimo": 0, "costo": 0, "precio_venta": 0, "activo": "on"}))
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(Producto.objects.filter(nombre="Intruso").exists())
