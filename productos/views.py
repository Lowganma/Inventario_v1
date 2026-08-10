from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from usuarios.permisos import dueno_required

from .forms import CategoriaForm, ProductoForm
from .models import Categoria, Producto


@login_required
def index(request):
    negocio = request.user.negocio
    busqueda = request.GET.get("buscar", "").strip()
    categoria_seleccionada = request.GET.get("categoria", "").strip()

    # El queryset base aplica el aislamiento multiempresa antes de cualquier filtro.
    productos_del_negocio = Producto.objects.filter(negocio=negocio).select_related(
        "categoria"
    )
    productos = productos_del_negocio
    if busqueda:
        productos = productos.filter(
            Q(nombre__icontains=busqueda)
            | Q(codigo__icontains=busqueda)
            | Q(categoria__nombre__icontains=busqueda)
        )
    if categoria_seleccionada.isdigit():
        productos = productos.filter(categoria_id=categoria_seleccionada)

    valor = ExpressionWrapper(
        F("stock") * F("costo"),
        output_field=DecimalField(max_digits=20, decimal_places=2),
    )
    indicadores = productos_del_negocio.aggregate(
        total=Count("id"),
        stock_bajo=Count("id", filter=Q(stock__lte=F("stock_minimo"))),
        valor_total=Coalesce(
            Sum(valor),
            Decimal("0.00"),
            output_field=DecimalField(max_digits=20, decimal_places=2),
        ),
    )
    return render(
        request,
        "productos/index.html",
        {
            "productos": productos,
            "categorias": Categoria.objects.filter(negocio=negocio, activa=True),
            "buscar": busqueda,
            "categoria_seleccionada": categoria_seleccionada,
            **indicadores,
        },
    )


@login_required
def detalle(request, producto_id):
    producto = get_object_or_404(
        Producto.objects.select_related("categoria"),
        id=producto_id,
        negocio=request.user.negocio,
    )
    return render(request, "productos/detalle.html", {"producto": producto})


def _guardar_producto(request, producto=None):
    formulario = ProductoForm(
        request.POST or None,
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