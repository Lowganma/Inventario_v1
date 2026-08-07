from django.shortcuts import render
from django.contrib import messages
from django.core.exceptions import ValidationError

from .models import Compra
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404,redirect
from .forms import CompraForm, DetalleCompraFormSet
from .services.compras import registrar_compra


# ============================================================
# LISTADO DE COMPRAS
# ============================================================

@login_required
def lista_compras(request):
    """
    Lista únicamente las compras pertenecientes
    al negocio del usuario autenticado.
    """

    compras = (
        Compra.objects.filter(
            negocio=request.user.negocio,
        )
        .select_related("usuario")
        .prefetch_related("detalles")
        .order_by("-fecha", "-id")
    )

    contexto = {
        "compras": compras,
    }

    return render(
        request,
        "compras/lista_compras.html",
        contexto,
    )


# ============================================================
# REGISTRAR NUEVA COMPRA
# ============================================================

@login_required
def crear_compra(request):
    """
    Registra una compra y actualiza el inventario
    únicamente cuando todos los datos son válidos.
    """

    negocio = request.user.negocio

    if request.method == "POST":

        formulario = CompraForm(
            request.POST,
        )

        detalles = DetalleCompraFormSet(
            request.POST,
            form_kwargs={
                "negocio": negocio,
            },
        )

        if formulario.is_valid() and detalles.is_valid():

            try:

                compra = registrar_compra(
                    negocio=negocio,
                    usuario=request.user,
                    notas=formulario.cleaned_data.get(
                        "notas",
                        "",
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
                        "No fue posible registrar la compra. "
                        "No se realizaron cambios en el inventario."
                    ),
                )

            else:

                messages.success(
                    request,
                    (
                        f"Compra #{compra.id} registrada correctamente. "
                        "El stock fue actualizado."
                    ),
                )

                return redirect(
                    "compras:detalle",
                    compra_id=compra.id,
                )

        else:

            messages.error(
                request,
                (
                    "Revisa los datos de la compra. "
                    "Hay campos pendientes o incorrectos."
                ),
            )

    else:

        formulario = CompraForm()

        detalles = DetalleCompraFormSet(
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
        "compras/crear_compra.html",
        contexto,
    )

# ============================================================
# DETALLE DE COMPRA
# ============================================================

@login_required
def detalle_compra(request, compra_id):
    """
    Muestra una compra perteneciente exclusivamente
    al negocio del usuario autenticado.
    """

    compra = get_object_or_404(
        Compra.objects.prefetch_related(
            "detalles__producto"
        ),
        id=compra_id,
        negocio=request.user.negocio,
    )

    contexto = {
        "compra": compra,
    }

    return render(
        request,
        "compras/detalle_compra.html",
        contexto,
    )