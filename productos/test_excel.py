from decimal import Decimal
from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from openpyxl import Workbook, load_workbook

from usuarios.models import Negocio, PerfilUsuario
from .models import Categoria, Producto


class CargaExcelTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user("papeleria")
        self.negocio = Negocio.objects.create(propietario=self.usuario, nombre="Papelería")
        self.client.force_login(self.usuario)
        self.url = reverse("productos:importar_excel")
        self.categoria = Categoria.objects.create(negocio=self.negocio, nombre="Escolar")
        self.lapiz = Producto.objects.create(negocio=self.negocio, categoria=self.categoria,
                                             nombre="Lápiz", codigo="001", precio_venta=2, stock=12)

    def archivo(self, filas):
        libro = Workbook()
        for fila in filas:
            libro.active.append(fila)
        datos = BytesIO()
        libro.save(datos)
        return datos.getvalue()

    def revisar(self, contenido):
        return self.client.post(self.url, {"archivo": SimpleUploadedFile("productos.xlsx", contenido)})

    def confirmar(self, respuesta):
        return self.client.post(self.url, {"accion": "confirmar", "token": respuesta.context["token"]})

    def descargar(self, modo):
        return self.client.get(reverse("productos:descargar_excel", args=[modo]))

    def test_demo_revisa_sin_escribir_y_crea_presentacion_para_fisico(self):
        respuesta = self.revisar(self.descargar("ejemplo").content)
        self.assertContains(respuesta, "Confirmar y guardar")
        self.assertEqual(Producto.objects.count(), 1)
        self.assertEqual(Categoria.objects.count(), 1)
        self.assertRedirects(self.confirmar(respuesta), reverse("productos:index"))
        nuevo = Producto.objects.get(codigo="DEMO-001")
        self.assertEqual(nuevo.stock, 18)
        self.assertEqual(nuevo.presentaciones.get().precio_venta, 3)
        self.assertFalse(Producto.objects.get(codigo="DEMO-002").presentaciones.exists())
        self.assertContains(self.confirmar(respuesta), "revisión ya no está disponible")
        repetida = self.revisar(self.descargar("ejemplo").content)
        self.assertEqual(repetida.context["revision"].resumen["Sin cambios"], 2)

    def test_editar_varios_precios_sin_reponer_stock_y_columna_vacia_conserva(self):
        self.lapiz.presentaciones.create(nombre="Unidad", cantidad_unidades=1, precio_venta=2)
        respuesta = self.revisar(self.archivo([
            ["Código", "Precio de venta (USD)", "Stock final"], ["001", "2,50", None],
        ]))
        self.confirmar(respuesta)
        self.lapiz.refresh_from_db()
        self.assertEqual(self.lapiz.stock, 12)
        self.assertEqual(self.lapiz.precio_venta, Decimal("2.50"))
        self.assertEqual(self.lapiz.presentaciones.get().precio_venta, Decimal("2.50"))

    def test_un_error_bloquea_todo_el_archivo(self):
        respuesta = self.revisar(self.archivo([
            ["Código", "Stock final"], ["001", 9], ["NO-EXISTE", 3],
        ]))
        self.assertContains(respuesta, "Fila 3:")
        self.assertNotContains(respuesta, "Confirmar y guardar")
        self.lapiz.refresh_from_db()
        self.assertEqual(self.lapiz.stock, 12)

    def test_stock_es_absoluto_y_detecta_cambio_entre_revision_y_confirmacion(self):
        contenido = self.archivo([["ID", "Stock final"], [self.lapiz.pk, 8]])
        respuesta = self.revisar(contenido)
        Producto.objects.filter(pk=self.lapiz.pk).update(stock=10)
        self.assertContains(self.confirmar(respuesta), "El catálogo cambió")
        self.lapiz.refresh_from_db()
        self.assertEqual(self.lapiz.stock, 10)
        self.confirmar(self.revisar(contenido))
        self.lapiz.refresh_from_db()
        self.assertEqual(self.lapiz.stock, 8)

    def test_exportar_y_editar_servicio_sin_codigo(self):
        self.lapiz.codigo = ""
        self.lapiz.tipo = "servicio"
        self.lapiz.stock = 0
        self.lapiz.nombre = "=Copias"
        self.lapiz.save()
        libro = load_workbook(BytesIO(self.descargar("catalogo").content))
        celda = libro["Productos"]["B2"]
        self.assertEqual(celda.value, "=Copias")
        self.assertEqual(celda.data_type, "s")
        self.assertIsNone(libro["Productos"]["F2"].value)
        libro["Productos"]["D2"] = 4
        buf = BytesIO()
        libro.save(buf)
        self.confirmar(self.revisar(buf.getvalue()))
        self.lapiz.refresh_from_db()
        self.assertEqual(self.lapiz.precio_venta, 4)

    def test_codigos_repetidos_y_formulas_rechazados(self):
        respuesta = self.revisar(self.archivo([["Código", "Stock final"], ["001", 1], ["001", 2]]))
        self.assertContains(respuesta, "más de una vez")
        respuesta = self.revisar(self.archivo([["Código", "Stock final"], ["001", "=2+2"]]))
        self.assertContains(respuesta, "fórmula")

    def test_archivo_ilegible_y_plantilla_vacia(self):
        self.assertContains(self.revisar(b"Excel"), "No se pudo leer")
        self.assertContains(self.revisar(self.descargar("plantilla").content), "no contiene productos")

    def test_aislamiento_y_permiso_de_escritura(self):
        otro = User.objects.create_user("otro")
        Negocio.objects.create(propietario=otro, nombre="Otro")
        self.client.force_login(otro)
        respuesta = self.revisar(self.archivo([["ID", "Precio de venta (USD)"], [self.lapiz.pk, 5]]))
        self.assertContains(respuesta, "no corresponde")
        libro = load_workbook(BytesIO(self.descargar("catalogo").content))
        self.assertEqual(libro.active.max_row, 1)
        empleado = User.objects.create_user("empleado")
        PerfilUsuario.objects.create(usuario=empleado, negocio=self.negocio, rol="empleado")
        self.client.force_login(empleado)
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(self.descargar("catalogo").status_code, 403)
