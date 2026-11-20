from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from usuarios.models import Negocio

from .models import Categoria, Producto


@override_settings(DEBUG=False)
class FotosProductoTests(TestCase):
    def setUp(self):
        carpeta = TemporaryDirectory()
        self.addCleanup(carpeta.cleanup)
        self.carpeta = Path(carpeta.name)
        self.enterContext(override_settings(MEDIA_ROOT=self.carpeta))
        usuario = User.objects.create_user("papeleria")
        negocio = Negocio.objects.create(propietario=usuario, nombre="Papelería")
        categoria = Categoria.objects.create(negocio=negocio, nombre="Escolar")
        self.client.force_login(usuario)

        foto = BytesIO()
        Image.new("RGB", (2, 2), "green").save(foto, format="PNG")
        self.contenido = foto.getvalue()
        respuesta = self.client.post(reverse("productos:crear"), {
            "categoria": categoria.pk, "nombre": "Cuaderno", "stock": 3,
            "stock_minimo": 0, "costo": 1, "precio_venta": 2, "activo": "on",
            "imagen": SimpleUploadedFile("cuaderno.png", self.contenido, content_type="image/png"),
        })
        self.assertEqual(respuesta.status_code, 302)
        self.producto = Producto.objects.get(negocio=negocio, nombre="Cuaderno")

    def test_misma_url_lee_el_archivo_guardado_con_debug_desactivado(self):
        imagen = self.producto.imagen
        self.assertEqual(imagen.name, "productos/cuaderno.png")
        self.assertEqual((self.carpeta / imagen.name).read_bytes(), self.contenido)
        self.assertContains(self.client.get(reverse("productos:detalle", args=[self.producto.pk])), imagen.url)
        respuesta = self.client.get(imagen.url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta["Content-Type"], "image/png")
        self.assertEqual(b"".join(respuesta.streaming_content), self.contenido)

    def test_foto_ausente(self):
        Path(self.producto.imagen.path).unlink()
        self.assertEqual(self.client.get(self.producto.imagen.url).status_code, 404)

    def test_acceso_a_la_foto_desde_otra_sesion(self):
        self.client.logout()
        self.assertEqual(self.client.get(self.producto.imagen.url).status_code, 302)
        otro = User.objects.create_user("segunda-tienda")
        Negocio.objects.create(propietario=otro, nombre="Otra tienda")
        self.client.force_login(otro)
        self.assertEqual(self.client.get(self.producto.imagen.url).status_code, 404)
