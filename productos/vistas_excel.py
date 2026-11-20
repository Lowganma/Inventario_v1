from uuid import uuid4

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError, OperationalError, transaction
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from usuarios.permisos import dueno_required
from .excel import COLUMNAS, leer_archivo, libro_productos, revisar
from .guardado import guardar_producto
from .models import Categoria

SESION = "productos_revision_excel"


def valor_visible(campo, valor):
    if campo in ("precio_venta", "costo") and valor != "":
        return format(valor, ".2f").replace(".", ",")
    return valor


@login_required
@dueno_required
@require_GET
def descargar(request, modo):
    if modo not in ("plantilla", "ejemplo", "catalogo"):
        raise Http404
    respuesta = HttpResponse(
        libro_productos(request.negocio, modo),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    respuesta["Content-Disposition"] = f'attachment; filename="organiza-te-{modo}.xlsx"'
    return respuesta


@transaction.atomic
def confirmar(negocio, pendiente):
    revision = revisar(negocio, pendiente["registros"], bloquear=True)
    if revision.errores or revision.firma() != pendiente["firma"]:
        raise ValidationError("El catálogo cambió después de la revisión. Vuelve a subir el Excel para ver los valores actuales.")
    creadas = {}
    for fila in revision.filas:
        if fila.accion == "Sin cambios":
            continue
        if fila.categoria.pk is None:
            nombre = fila.categoria.nombre
            if nombre.casefold() not in creadas:
                creadas[nombre.casefold()] = Categoria.objects.create(negocio=negocio, nombre=nombre)
            fila.producto.categoria = creadas[nombre.casefold()]
        campos = [*fila.cambios, "fecha_actualizacion"] if fila.producto.pk else None
        cambio_precio = fila.cambios.get("precio_venta")
        precio_anterior = cambio_precio[0] if fila.producto.pk and cambio_precio else None
        guardar_producto(fila.producto, campos=campos, precio_anterior=precio_anterior)
    return revision.resumen


@login_required
@dueno_required
@require_http_methods(["GET", "POST"])
def importar(request):
    contexto = {}
    if request.method == "POST":
        try:
            if request.POST.get("accion") == "confirmar":
                pendiente = request.session.get(SESION)
                if (not pendiente or pendiente["token"] != request.POST.get("token")
                        or pendiente["negocio"] != request.negocio.pk or pendiente["usuario"] != request.user.pk):
                    raise ValidationError("Esta revisión ya no está disponible. Vuelve a subir el archivo.")
                totales = confirmar(request.negocio, pendiente)
                request.session.pop(SESION, None)
                messages.success(request, f"Excel aplicado. Productos creados: {totales['Crear']}. Actualizados: {totales['Actualizar']}.")
                return redirect("productos:index")
            request.session.pop(SESION, None)
            registros = leer_archivo(request.FILES.get("archivo"))
            revision = revisar(request.negocio, registros)
            contexto["revision"] = revision
            contexto["categorias_nuevas"] = sorted({
                f.categoria.nombre for f in revision.filas if not f.categoria.pk
            })
            contexto["vista_previa"] = [
                (f, [(COLUMNAS[k], valor_visible(k, antes), valor_visible(k, despues))
                     for k, (antes, despues) in f.cambios.items()])
                for f in revision.filas
            ]
            if not revision.errores and revision.pendientes:
                token = uuid4().hex
                request.session[SESION] = dict(registros=registros, firma=revision.firma(),
                                               token=token, usuario=request.user.pk, negocio=request.negocio.pk)
                contexto["token"] = token
        except ValidationError as exc:
            contexto["error"] = " ".join(exc.messages)
        except IntegrityError:
            contexto["error"] = "No se aplicó la carga. Comprueba los códigos, nombres y presentaciones y vuelve a revisar el Excel."
        except OperationalError as exc:
            if "locked" not in str(exc).lower():
                raise
            contexto["error"] = "El inventario está ocupado. Vuelve a revisar el archivo en un momento."
    return render(request, "productos/importar_excel.html", contexto)
