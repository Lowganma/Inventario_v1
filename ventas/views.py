
from django.http import JsonResponse
from productos.models import Producto
from .models import Venta

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError

from decimal import Decimal
from .services.ventas import registrar_venta   

from .forms import VentaForm, DetalleVentaFormSet
# ============================================================
# LISTADO DE VENTAS
# ============================================================

@login_required
def lista_ventas(request):
    """
    Muestra únicamente las ventas pertenecientes
    al negocio del usuario autenticado.
    """

    ventas = (
        Venta.objects
        .filter(
            negocio=request.user.negocio,
        )
        .select_related(
            "cliente",
            "usuario",
            "cuenta_por_cobrar",
        )
        .prefetch_related(
            "detalles",
        )
        .order_by(
            "-fecha",
            "-id",
        )
    )

    contexto = {
        "ventas": ventas,
    }

    return render(
        request,
        "ventas/lista_ventas.html",
        contexto,
    )
# ============================================================
# REGISTRAR NUEVA VENTA
# ============================================================

@login_required
def crear_venta(request):
    """
    Registra una venta y descuenta automáticamente
    los productos del inventario.
    """

    negocio = request.user.negocio


    if request.method == "POST":

        formulario = VentaForm(
            request.POST,
            negocio=negocio,
        )

        detalles = DetalleVentaFormSet(
            request.POST,
            form_kwargs={
                "negocio": negocio,
            },
        )


        if (
            formulario.is_valid()
            and detalles.is_valid()
        ):

            try:

                venta = registrar_venta(
                    negocio=negocio,
                    usuario=request.user,

                    cliente=(
                        formulario.cleaned_data.get(
                            "cliente"
                        )
                    ),

                    tipo_pago=(
                        formulario.cleaned_data[
                            "tipo_pago"
                        ]
                    ),

                    metodo_pago=(
                        formulario.cleaned_data.get(
                            "metodo_pago",
                            "",
                        )
                    ),

                    descuento=(
                        formulario.cleaned_data.get(
                            "descuento"
                        )
                        or Decimal("0.00")
                    ),

                    notas=(
                        formulario.cleaned_data.get(
                            "notas",
                            "",
                        )
                    ),

                    detalles=detalles.cleaned_data,
                )


            except ValidationError as error:

                messages.error(
                    request,
                    " ".join(error.messages),
                )


            except Exception:

                messages.error(
                    request,
                    (
                        "No fue posible registrar la venta. "
                        "No se modificó el inventario."
                    ),
                )


            else:

                if venta.tipo_pago == "fiado":

                    messages.success(
                        request,
                        (
                            f"Venta #{venta.id} registrada. "
                            "Se creó una cuenta por cobrar."
                        ),
                    )

                else:

                    messages.success(
                        request,
                        (
                            f"Venta #{venta.id} registrada "
                            "correctamente."
                        ),
                    )


                return redirect(
                    "ventas:detalle",
                    venta_id=venta.id,
                )


        else:

            messages.error(
                request,
                (
                    "Revisa la información de la venta. "
                    "Hay campos pendientes o incorrectos."
                ),
            )


    else:

        formulario = VentaForm(
            negocio=negocio,
        )

        detalles = DetalleVentaFormSet(
            form_kwargs={
                "negocio": negocio,
            },
        )


    contexto = {
        "formulario": formulario,
        "detalles": detalles,
    }


    return render(
        request,
        "ventas/crear_venta.html",
        contexto,
    )

# ============================================================
# DETALLE DE VENTA
# ============================================================

@login_required
def detalle_venta(request, venta_id):
    """
    Muestra el detalle completo de una venta.

    La consulta está limitada al negocio del usuario
    autenticado para mantener el aislamiento multiempresa.
    """

    venta = get_object_or_404(
        Venta.objects
        .select_related(
            "cliente",
            "usuario",
            "cuenta_por_cobrar",
        )
        .prefetch_related(
            "detalles__producto",
        ),
        id=venta_id,
        negocio=request.user.negocio,
    )

    contexto = {
        "venta": venta,
    }

    return render(
        request,
        "ventas/detalle_venta.html",
        contexto,
    )

# ============================================================
# Datos DE PRODUCTO
# ============================================================


@login_required
def datos_producto(request, producto_id):
    """
    Devuelve información comercial de un producto.

    La consulta está limitada al negocio del usuario para
    impedir obtener datos de productos de otra organización.
    """

    producto = get_object_or_404(
        Producto,
        id=producto_id,
        negocio=request.user.negocio,
        activo=True,
    )

    return JsonResponse(
        {
            "id": producto.id,
            "nombre": producto.nombre,
            "stock": producto.stock,
            "precio_venta": str(producto.precio_venta),
            "costo": str(producto.costo),
        }
    )