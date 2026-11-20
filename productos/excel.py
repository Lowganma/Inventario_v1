"""Plantilla e intercambio de datos del catálogo de un solo negocio."""
from collections import Counter
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from io import BytesIO
import json
import unicodedata
from zipfile import BadZipFile, ZipFile
from xml.etree.ElementTree import ParseError

from defusedxml.common import DefusedXmlException
from django.core.exceptions import ValidationError
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.utils.exceptions import InvalidFileException

from .models import Categoria, Producto

COLUMNAS = {
    "codigo": "Código", "nombre": "Nombre", "categoria": "Categoría",
    "precio_venta": "Precio de venta (USD)", "costo": "Costo (USD)",
    "stock": "Stock final", "stock_minimo": "Stock mínimo", "tipo": "Tipo",
    "unidad_base": "Unidad", "id": "ID", "stock_actual": "Stock actual (consulta)",
}
NUMERICOS = {"precio_venta", "costo", "stock", "stock_minimo"}
LIMITE_FILAS = 500


def clave(texto):
    return "".join(c for c in unicodedata.normalize("NFKD", str(texto).strip().casefold())
                   if not unicodedata.combining(c))


def libro_productos(negocio, modo):
    libro = Workbook()
    hoja = libro.active
    hoja.title = "Productos"
    hoja.append(list(COLUMNAS.values()))
    for celda in hoja[1]:
        celda.fill = PatternFill("solid", fgColor="006553")
        celda.font = Font(color="FFFFFF", bold=True)
    for columna, ancho in enumerate((19, 32, 24, 24, 16, 16, 16, 16, 16, 12, 28), 1):
        hoja.column_dimensions[get_column_letter(columna)].width = ancho
    hoja.column_dimensions["A"].number_format = "@"
    hoja.freeze_panes = "B2"
    if modo == "ejemplo":
        hoja.append(["DEMO-001", "Cuaderno rayado", "Papelería", 3, 1.5, 18, 4, "Producto", "Unidad"])
        hoja.append(["DEMO-002", "Copia en blanco y negro", "Copias", 0.10, 0.02, None, None, "Servicio"])
    elif modo == "catalogo":
        productos = Producto.objects.filter(negocio=negocio).select_related("categoria")
        for n, p in enumerate(productos.iterator(), start=2):
            hoja.append([p.codigo, p.nombre, p.categoria.nombre, p.precio_venta, p.costo,
                         None, p.stock_minimo if p.tipo == "producto" else None, p.tipo,
                         p.unidad_base, p.pk, p.stock if p.tipo == "producto" else None])
            # Los nombres y códigos son texto literal, incluso si comienzan por '='.
            for i in (1, 2, 3):
                hoja.cell(n, i).data_type = "s"
    hoja.auto_filter.ref = hoja.dimensions
    ayuda = libro.create_sheet("Guía")
    ayuda.column_dimensions["A"].width = 105
    for linea in (
        "organiza-te · Productos",
        "Para crear, llena Nombre, Categoría y Precio de venta (USD). Puedes agregar un código como texto.",
        "Para actualizar, conserva el ID de tu catálogo o escribe un código existente. Puedes subir solo esas columnas y los cambios.",
        "Una celda vacía conserva el valor actual. Stock final reemplaza la existencia; Stock actual solo sirve de consulta.",
        "En productos nuevos, costo y existencias empiezan en cero. Una categoría nueva se muestra en la revisión.",
        "Tipos: producto o servicio. Unidades: unidad, kg, g, litro, ml o metro. Los servicios no llevan existencias.",
        "Mantén el tipo y la unidad de los productos existentes. Edita fotos y presentaciones desde su ficha.",
        f"Usa valores en lugar de fórmulas. Puedes importar hasta {LIMITE_FILAS} filas de productos por archivo.",
    ):
        ayuda.append([linea])
    salida = BytesIO()
    libro.save(salida)
    return salida.getvalue()


def leer_archivo(archivo):
    if not archivo or not archivo.name.lower().endswith(".xlsx"):
        raise ValidationError("Selecciona un archivo de Excel con extensión .xlsx.")
    if archivo.size > 3 * 1024 * 1024:
        raise ValidationError("El archivo supera 3 MB. Divide el catálogo en varios archivos.")
    libro = None
    try:
        with ZipFile(archivo) as zip_excel:
            partes = zip_excel.infolist()
            if len(partes) > 500 or sum(p.file_size for p in partes) > 16 * 1024 * 1024:
                raise ValidationError("El libro es demasiado grande. Usa una copia de la plantilla.")
        archivo.seek(0)
        libro = load_workbook(archivo, read_only=True, keep_links=False)
        hoja = libro["Productos"] if "Productos" in libro.sheetnames else libro.worksheets[0]
        if (hoja.max_column or 0) > 32:
            raise ValidationError("La hoja contiene demasiadas columnas. Usa los encabezados de la plantilla.")
        hoja.reset_dimensions()
        filas = hoja.iter_rows(max_col=32)
        encabezado = next(filas, ())
        campos = {clave(nombre): campo for campo, nombre in COLUMNAS.items()}
        indices = {}
        for posicion, celda in enumerate(encabezado):
            if celda.value is None:
                continue
            campo = campos.get(clave(celda.value))
            if not campo or campo in indices.values():
                raise ValidationError(f"Encabezado desconocido o repetido: {str(celda.value)[:80]}. Usa los nombres de la plantilla.")
            indices[posicion] = campo
        if not {"id", "codigo", "nombre"}.intersection(indices.values()):
            raise ValidationError("Incluye un encabezado Nombre, Código o ID.")
        registros = []
        for numero, fila in enumerate(filas, start=2):
            if numero > LIMITE_FILAS + 1:
                raise ValidationError(f"Usa hasta {LIMITE_FILAS} filas por archivo y elimina las filas vacías finales.")
            registro = {}
            for i, celda in enumerate(fila):
                if celda.value is None or not str(celda.value).strip():
                    continue
                if i not in indices:
                    raise ValidationError(f"Fila {numero}: hay datos en una columna sin encabezado.")
                campo = indices[i]
                if campo == "stock_actual":
                    continue
                if celda.data_type in ("f", "e"):
                    raise ValidationError(f"Fila {numero}, {COLUMNAS[campo]}: pega el valor en lugar de una fórmula o error.")
                valor = str(celda.value).strip()
                if len(valor) > 255:
                    raise ValidationError(f"Fila {numero}, {COLUMNAS[campo]}: el valor es demasiado largo.")
                registro[campo] = valor
            if registro:
                registros.append([numero, registro])
        if not registros:
            raise ValidationError("La hoja no contiene productos. Escribe al menos una fila debajo de los encabezados.")
        return registros
    except (BadZipFile, KeyError, IndexError, OSError, ValueError, TypeError,
            ParseError, InvalidFileException, DefusedXmlException, RuntimeError) as exc:
        raise ValidationError("No se pudo leer el libro. Guárdalo como .xlsx con Excel o LibreOffice.") from exc
    finally:
        if libro:
            libro.close()


@dataclass
class Fila:
    numero: int
    accion: str
    producto: Producto
    categoria: Categoria
    cambios: dict = field(default_factory=dict)


@dataclass
class Revision:
    filas: list = field(default_factory=list)
    errores: list = field(default_factory=list)

    def firma(self):
        datos = [(r.numero, r.accion, r.producto.pk, r.producto.nombre, r.producto.codigo, r.categoria.pk,
                  r.categoria.nombre, r.cambios) for r in self.filas]
        return sha256(json.dumps(datos, sort_keys=True, default=str).encode()).hexdigest()

    @property
    def resumen(self):
        cantidades = Counter(r.accion for r in self.filas)
        return {k: cantidades[k] for k in ("Crear", "Actualizar", "Sin cambios")}

    @property
    def pendientes(self):
        return any(r.accion != "Sin cambios" for r in self.filas)


def interpretar(campo, valor):
    if campo in NUMERICOS:
        try:
            cantidad = Decimal(valor.replace(",", "."))
            if not cantidad.is_finite() or cantidad < 0 or cantidad.adjusted() > 14 or cantidad.as_tuple().exponent < -2:
                raise ValueError
            return cantidad
        except (InvalidOperation, ValueError):
            raise ValidationError(f"{COLUMNAS[campo]}: escribe un número positivo o cero con hasta dos decimales.")
    if campo in ("unidad_base", "tipo"):
        opciones = Producto.UNIDADES if campo == "unidad_base" else Producto.TIPOS
        for codigo, nombre in opciones:
            if clave(valor) in (clave(codigo), clave(nombre)):
                return codigo
        raise ValidationError(f"{COLUMNAS[campo]}: usa una de estas opciones: {', '.join(k for k, _ in opciones)}.")
    return valor


def revisar(negocio, registros, bloquear=False):
    revision = Revision()
    catalogo = Producto.objects.filter(negocio=negocio)
    categorias = Categoria.objects.filter(negocio=negocio)
    if bloquear:
        catalogo = catalogo.select_for_update()
        categorias = categorias.select_for_update()
    usados, codigos, nombres = set(), set(), set()
    for numero, valores in registros:
        try:
            fila = preparar_fila(negocio, catalogo, categorias, numero, valores)
            producto = fila.producto
            if ((producto.pk and producto.pk in usados) or
                    (producto.codigo and producto.codigo in codigos) or producto.nombre.casefold() in nombres):
                raise ValidationError("Este producto, nombre o código aparece más de una vez en la hoja.")
            usados.add(producto.pk)
            codigos.add(producto.codigo)
            nombres.add(producto.nombre.casefold())
            revision.filas.append(fila)
        except ValidationError as exc:
            revision.errores.append(f"Fila {numero}: {' '.join(exc.messages)}")
    return revision


def preparar_fila(negocio, catalogo, categorias, numero, valores):
    producto = None
    if "id" in valores:
        identificador = valores["id"]
        if not identificador.isascii() or not identificador.isdecimal() or len(identificador) > 18:
            raise ValidationError("ID inválido. Conserva el ID que aparece en tu catálogo.")
        producto = catalogo.filter(pk=identificador).first()
        if not producto:
            raise ValidationError("El ID no corresponde a un producto de este negocio.")
    elif "codigo" in valores:
        producto = catalogo.filter(codigo=valores["codigo"]).first()
    nuevo = producto is None
    if nuevo:
        faltan = [COLUMNAS[c] for c in ("nombre", "categoria", "precio_venta") if c not in valores]
        if faltan:
            raise ValidationError(f"Producto nuevo. Completa {', '.join(faltan)} o verifica el código.")
        producto = Producto(negocio=negocio)
    categoria = producto.categoria if producto.categoria_id else None
    if "categoria" in valores:
        opciones = list(categorias.filter(nombre__iexact=valores["categoria"])[:2])
        if len(opciones) > 1:
            raise ValidationError("Hay dos categorías con ese nombre. Unifica sus nombres antes de importar.")
        categoria = opciones[0] if opciones else Categoria(negocio=negocio, nombre=valores["categoria"])
        if not categoria.activa and categoria.pk != producto.categoria_id:
            raise ValidationError("La categoría está inactiva.")
    cambios = {}
    if categoria.pk != producto.categoria_id or nuevo:
        cambios["categoria"] = (producto.categoria.nombre if producto.categoria_id else "", categoria.nombre)
    producto.categoria = categoria
    for campo, valor in valores.items():
        if campo in ("id", "categoria"):
            continue
        anterior = getattr(producto, campo)
        actual = interpretar(campo, valor)
        if not nuevo and campo in ("tipo", "unidad_base") and actual != anterior:
            raise ValidationError(f"Cambia {COLUMNAS[campo].lower()} desde la ficha para revisar sus presentaciones.")
        if anterior != actual or nuevo:
            cambios[campo] = (anterior if not nuevo else "", actual)
        setattr(producto, campo, actual)
    if producto.tipo == "servicio" and any(c in valores and getattr(producto, c) != 0 for c in ("stock", "stock_minimo")):
        raise ValidationError("Los servicios no llevan existencias. Deja sus columnas de stock vacías.")
    if catalogo.filter(nombre__iexact=producto.nombre).exclude(pk=producto.pk).exists():
        raise ValidationError("Ya existe ese nombre. Para actualizarlo usa su ID o código.")
    # Una categoría nueva solo se crea después de confirmar.
    producto.full_clean(exclude=[] if categoria.pk else ["categoria"])
    return Fila(numero, "Crear" if nuevo else ("Actualizar" if cambios else "Sin cambios"),
                producto, categoria, cambios)
