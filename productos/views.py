from decimal import Decimal

from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from usuarios.permisos import dueno_required

from .forms import CategoriaForm, ProductoForm, PresentacionProductoForm
from .models import Categoria, PresentacionProducto, Producto


@login_required
def index(request):
    negocio = request.user.negocio

    busqueda = request.GET.get("buscar", "").strip()
    categoria_seleccionada = request.GET.get(
        "categoria",
        "",
    ).strip()

    # Cantidad de registros por página.
    opciones_por_pagina = [10, 20, 50]

    try:
        por_pagina = int(
            request.GET.get("por_pagina", 10)
        )
    except (TypeError, ValueError):
        por_pagina = 10

    if por_pagina not in opciones_por_pagina:
        por_pagina = 10

    # =========================================================
    # QUERYSET BASE
    # =========================================================

    productos_del_negocio = (
        Producto.objects
        .filter(negocio=negocio)
        .select_related("categoria")
    )

    productos_filtrados = productos_del_negocio

    # =========================================================
    # BÚSQUEDA
    # =========================================================

    if busqueda:
        productos_filtrados = (
            productos_filtrados.filter(
                Q(nombre__icontains=busqueda)
                | Q(codigo__icontains=busqueda)
                | Q(
                    categoria__nombre__icontains=
                    busqueda
                )
            )
        )

    # =========================================================
    # CATEGORÍA
    # =========================================================

    if categoria_seleccionada.isdigit():
        productos_filtrados = (
            productos_filtrados.filter(
                categoria_id=categoria_seleccionada
            )
        )

    # =========================================================
    # INDICADORES GENERALES
    # =========================================================

    valor = ExpressionWrapper(
        F("stock") * F("costo"),
        output_field=DecimalField(
            max_digits=20,
            decimal_places=2,
        ),
    )

    indicadores = (
        productos_del_negocio.aggregate(
            total=Count("id"),

            stock_bajo=Count(
                "id",
                filter=Q(
                    stock__lte=F("stock_minimo")
                ),
            ),

            valor_total=Coalesce(
                Sum(valor),
                Decimal("0.00"),
                output_field=DecimalField(
                    max_digits=20,
                    decimal_places=2,
                ),
            ),
        )
    )

    # =========================================================
    # PAGINACIÓN
    # =========================================================

    paginador = Paginator(
        productos_filtrados,
        por_pagina,
    )

    numero_pagina = request.GET.get("page")

    pagina_productos = paginador.get_page(
        numero_pagina
    )


    # =========================================================
    # RESPUESTA AJAX
    # =========================================================


    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render(
            request,
            "productos/_tabla_productos.html",
            {
                "productos": pagina_productos,
                "buscar": busqueda,
                "categoria_seleccionada": categoria_seleccionada,
                "por_pagina": por_pagina,
            },
        )

    # =========================================================
    # RENDER
    # =========================================================

    return render(
        request,
        "productos/index.html",
        {
            "productos": pagina_productos,

            "categorias": Categoria.objects.filter(
                negocio=negocio,
                activa=True,
            ),

            "buscar": busqueda,

            "categoria_seleccionada":
                categoria_seleccionada,

            "por_pagina": por_pagina,

            "opciones_por_pagina":
                opciones_por_pagina,

            "paginador": paginador,

            **indicadores,
        },
    )


@login_required
def detalle(request, producto_id):
    producto = get_object_or_404(
        Producto.objects
        .select_related("categoria")
        .prefetch_related("presentaciones"),
        id=producto_id,
        negocio=request.user.negocio,
    )

    formulario_presentacion = (
        PresentacionProductoForm()
    )

    return render(
        request,
        "productos/detalle.html",
        {
            "producto": producto,
            "formulario_presentacion":
                formulario_presentacion,
        },
    )


def _guardar_producto(request, producto=None):
    formulario = ProductoForm(
        request.POST or None,
        request.FILES or None,
        instance=producto,
        negocio=request.user.negocio,
    )
    if request.method == "POST" and formulario.is_valid():
        producto = formulario.save(commit=False)
        # El negocio procede siempre de la sesión, nunca de datos enviados por el cliente.
        producto.negocio = request.user.negocio
        producto.full_clean()
        producto.save()
        messages.success(request, "Producto guardado correctamente.")
        return redirect("productos:detalle", producto_id=producto.id)
    if producto.tipo == "producto":

        PresentacionProducto.objects.get_or_create(
            producto=producto,
            cantidad_unidades=Decimal("1.000"),
            defaults={
                "nombre":
                    producto.get_unidad_base_display(),
                "precio_venta":
                    producto.precio_venta,
            },
    )
    return render(
        request,
        "productos/producto_form.html",
        {"formulario": formulario, "producto": producto},
    )




@login_required
@dueno_required
def crear_producto(request):
    return _guardar_producto(request)


@login_required
@dueno_required
def editar_producto(request, producto_id):
    producto = get_object_or_404(
        Producto, id=producto_id, negocio=request.user.negocio
    )
    return _guardar_producto(request, producto)


@login_required
def lista_categorias(request):
    categorias = (
        Categoria.objects.filter(negocio=request.user.negocio)
        .annotate(cantidad_productos=Count("productos"))
        .order_by("nombre")
    )
    return render(
        request, "productos/categorias.html", {"categorias": categorias}
    )


def _guardar_categoria(request, categoria=None):
    formulario = CategoriaForm(
        request.POST or None,
        instance=categoria,
        negocio=request.user.negocio,
    )
    if request.method == "POST" and formulario.is_valid():
        categoria = formulario.save(commit=False)
        # La empresa se asigna en servidor para impedir suplantación por POST.
        categoria.negocio = request.user.negocio
        categoria.full_clean()
        categoria.save()
        messages.success(request, "Categoría guardada correctamente.")
        return redirect("productos:categorias")
    return render(
        request,
        "productos/categoria_form.html",
        {"formulario": formulario, "categoria": categoria},
    )


@login_required
def crear_categoria(request):
    return _guardar_categoria(request)


@login_required
def editar_categoria(request, categoria_id):
    categoria = get_object_or_404(
        Categoria, id=categoria_id, negocio=request.user.negocio
    )
    return _guardar_categoria(request, categoria)

@login_required
@dueno_required
@require_POST
def crear_categoria_rapida(request):
    formulario = CategoriaForm(
        request.POST,
        negocio=request.user.negocio,
    )

    if not formulario.is_valid():
        errores = {}

        for campo, mensajes in formulario.errors.items():
            errores[campo] = [str(mensaje) for mensaje in mensajes]

        return JsonResponse(
            {
                "ok": False,
                "errores": errores,
            },
            status=400,
        )

    categoria = formulario.save(commit=False)

    categoria.negocio = request.user.negocio
    categoria.full_clean()
    categoria.save()

    return JsonResponse(
        {
            "ok": True,
            "categoria": {
                "id": categoria.id,
                "nombre": categoria.nombre,
            },
        }
    )

@login_required
def datos_producto(request, producto_id):
    """
    Devuelve información comercial del producto para
    formularios dinámicos, respetando el negocio del usuario.
    """

    producto = get_object_or_404(
        Producto,
        id=producto_id,
        negocio=request.user.negocio,
    )

    return JsonResponse(
        {
            "id": producto.id,
            "nombre": producto.nombre,
            "stock": producto.stock,
            "costo": str(producto.costo),
            "precio_venta": str(producto.precio_venta),
        }
    )

@login_required
@dueno_required
@require_POST
def crear_presentacion(
    request,
    producto_id,
):
    producto = get_object_or_404(
        Producto,
        id=producto_id,
        negocio=request.user.negocio,
    )

    formulario = PresentacionProductoForm(
        request.POST
    )

    if formulario.is_valid():

        presentacion = formulario.save(
            commit=False
        )

        presentacion.producto = producto

        presentacion.full_clean()

        presentacion.save()

        messages.success(
            request,
            "Presentación agregada correctamente.",
        )

    else:

        messages.error(
            request,
            "Revisa los datos de la presentación.",
        )

    return redirect(
        "productos:detalle",
        producto_id=producto.id,
    )