from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from django.db.models import Q
from django.core.paginator import Paginator

from productos.models import Producto

from .forms import DetalleVentaFormSet, VentaForm
from .models import Venta
from .services.ventas import registrar_venta


@login_required
def lista_ventas(request):

    negocio = request.user.negocio

    # --------------------------------------------------------
    # PARÁMETROS
    # --------------------------------------------------------

    buscar = request.GET.get(
        "buscar",
        "",
    ).strip()

    fecha_desde = request.GET.get(
        "fecha_desde",
        "",
    )

    fecha_hasta = request.GET.get(
        "fecha_hasta",
        "",
    )

    try:
        por_pagina = int(
            request.GET.get(
                "por_pagina",
                10,
            )
        )
    except (TypeError, ValueError):
        por_pagina = 10

    if por_pagina not in [10, 20, 50]:
        por_pagina = 10


    # --------------------------------------------------------
    # TODAS LAS VENTAS DEL NEGOCIO
    # --------------------------------------------------------

    ventas_negocio = (
        Venta.objects
        .filter(
            negocio=negocio,
        )
        .select_related(
            "cliente",
            "usuario",
            "cuenta_por_cobrar",
        )
        .prefetch_related(
            "detalles__producto",
            "detalles__presentacion",
        )
        .order_by(
            "-fecha",
            "-id",
        )
    )


    # Datos generales de las tarjetas superiores.
    total_ventas = ventas_negocio.count()

    ultima_venta = ventas_negocio.first()


    # --------------------------------------------------------
    # BÚSQUEDA
    # --------------------------------------------------------

    ventas = ventas_negocio

    if buscar:

        filtro_busqueda = (
            Q(
                cliente__nombre__icontains=buscar
            )
            |
            Q(
                cliente__apellido__icontains=buscar
            )
            |
            Q(
                detalles__producto__nombre__icontains=buscar
            )
            |
            Q(
                referencia_pago__icontains=buscar
            )
            |
            Q(
                detalle_pago__icontains=buscar
            )
            |
            Q(
                notas__icontains=buscar
            )
        )

        # Si escribió un número también buscamos
        # directamente por número de venta.
        if buscar.isdigit():

            filtro_busqueda |= Q(
                numero=int(buscar)
            )

        ventas = ventas.filter(
            filtro_busqueda
        ).distinct()


    # --------------------------------------------------------
    # RANGO DE FECHAS
    # --------------------------------------------------------

    if fecha_desde:

        ventas = ventas.filter(
            fecha__date__gte=fecha_desde
        )


    if fecha_hasta:

        ventas = ventas.filter(
            fecha__date__lte=fecha_hasta
        )


    # --------------------------------------------------------
    # PAGINACIÓN
    # --------------------------------------------------------

    paginador = Paginator(
        ventas,
        por_pagina,
    )

    pagina = request.GET.get(
        "page",
        1,
    )

    ventas_paginadas = paginador.get_page(
        pagina
    )


    contexto = {

        "ventas":
            ventas_paginadas,

        "total_ventas":
            total_ventas,

        "ultima_venta":
            ultima_venta,

        "buscar":
            buscar,

        "fecha_desde":
            fecha_desde,

        "fecha_hasta":
            fecha_hasta,

        "por_pagina":
            por_pagina,

    }


    return render(
        request,
        "ventas/lista_ventas.html",
        contexto,
    )


@login_required
def crear_venta(request):
    negocio = request.user.negocio

    if request.method == "POST":
        formulario = VentaForm(request.POST, negocio=negocio)
        detalles = DetalleVentaFormSet(
            request.POST,
            form_kwargs={"negocio": negocio},
        )

        if formulario.is_valid() and detalles.is_valid():
            try:
                venta = registrar_venta(
                    negocio=negocio,
                    usuario=request.user,
                    cliente=formulario.cleaned_data.get("cliente"),
                    tipo_pago=formulario.cleaned_data["tipo_pago"],
                    metodo_pago=formulario.cleaned_data.get("metodo_pago", ""),
                    referencia_pago=formulario.cleaned_data.get("referencia_pago", ""),
                    detalle_pago=formulario.cleaned_data.get("detalle_pago", ""),
                    tipo_descuento=formulario.cleaned_data.get("tipo_descuento", ""),
                    valor_descuento=(
                        formulario.cleaned_data.get("valor_descuento")
                        or Decimal("0.00")
                    ),
                    notas=formulario.cleaned_data.get("notas", ""),
                    detalles=detalles.cleaned_data,
                )
            except ValidationError as error:
                messages.error(request, " ".join(error.messages))
            except Exception as error:
                print("ERROR registrar_venta:", repr(error))
                messages.error(
                    request,
                    "No fue posible registrar la venta. No se modificó el inventario.",
                )
            else:
                if venta.tipo_pago == "fiado":
                    messages.success(
                        request,
                        f"Venta #{venta.numero} registrada. Se creó una cuenta por cobrar.",
                    )
                else:
                    messages.success(
                        request,
                        f"Venta #{venta.numero} registrada correctamente.",
                    )
                return redirect("ventas:detalle", venta_id=venta.id)
        else:
            messages.error(
                request,
                "Revisa la información de la venta. Hay campos pendientes o incorrectos.",
            )
    else:
        formulario = VentaForm(negocio=negocio)
        detalles = DetalleVentaFormSet(form_kwargs={"negocio": negocio})

    # ============================================================
    # CATÁLOGO DE PRODUCTOS Y SERVICIOS
    # ============================================================

    productos_catalogo = (
        Producto.objects
        .filter(
            negocio=negocio,
            activo=True,
        )
        .select_related(
            "categoria"
        )
        .order_by(
            "nombre"
        )
    )
    categorias_catalogo = (
            productos_catalogo
            .values_list(
                "categoria__nombre",
                flat=True,
            )
            .distinct()
            .order_by("categoria__nombre")
        )


    return render(
        request,
        "ventas/crear_venta.html",
        {
            "formulario": formulario,
            "detalles": detalles,
            "productos_catalogo": productos_catalogo,
            "categorias_catalogo": categorias_catalogo,
        },
    )



@login_required
def detalle_venta(request, venta_id):
    venta = get_object_or_404(
        Venta.objects
        .select_related("cliente", "usuario", "cuenta_por_cobrar", "negocio")
        .prefetch_related("detalles__producto", "detalles__presentacion"),
        id=venta_id,
        negocio=request.user.negocio,
    )

    return render(request, "ventas/detalle_venta.html", {"venta": venta})


@login_required
def datos_producto(request, producto_id):
    producto = get_object_or_404(
        Producto,
        id=producto_id,
        negocio=request.user.negocio,
        activo=True,
    )

    presentaciones = (
        producto.presentaciones
        .filter(activa=True)
        .order_by("cantidad_unidades", "nombre")
    )

    return JsonResponse(
        {
            "id": producto.id,
            "nombre": producto.nombre,
            "tipo": producto.tipo,
            "imagen": producto.imagen.url if producto.imagen else None,
            "stock": str(producto.stock),
            "stock_mostrado": (
                producto.stock_con_unidad
                if producto.tipo == "producto"
                else "No aplica"
            ),
            "unidad_base": producto.unidad_base,
            "unidad_base_display": producto.get_unidad_base_display(),
            "precio_venta": str(producto.precio_venta),
            "costo": str(producto.costo),
            "presentaciones": [
                {
                    "id": presentacion.id,
                    "nombre": presentacion.nombre,
                    "cantidad": str(presentacion.cantidad_unidades),
                    "precio": (
                        str(presentacion.precio_venta)
                        if presentacion.precio_venta is not None
                        else None
                    ),
                }
                for presentacion in presentaciones
            ],
        }
    )
