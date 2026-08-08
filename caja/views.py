from decimal import Decimal
from django.contrib import messages

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render, redirect

from .models import MovimientoCaja
from .services.caja import registrar_movimiento
from .forms import MovimientoCajaForm


@login_required
def dashboard_caja(request):
    """
    Presenta el resumen financiero básico del negocio.
    """

    movimientos = MovimientoCaja.objects.filter(
        negocio=request.user.negocio,
    )

    ingresos = (
        movimientos
        .filter(tipo="ingreso")
        .aggregate(total=Sum("monto"))["total"]
        or Decimal("0.00")
    )

    egresos = (
        movimientos
        .filter(tipo="egreso")
        .aggregate(total=Sum("monto"))["total"]
        or Decimal("0.00")
    )

    saldo = ingresos - egresos



    # --------------------------------------------------------
# SALDOS POR MÉTODO DE PAGO
# --------------------------------------------------------

    metodos = [
        ("efectivo", "Efectivo"),
        ("transferencia", "Transferencia"),
        ("divisa", "Divisa"),
        ("otro", "Otro"),
    ]

    saldos_metodos = []

    for codigo, nombre in metodos:

        ingresos_metodo = (
            movimientos
            .filter(
                tipo="ingreso",
                metodo_pago=codigo,
            )
            .aggregate(total=Sum("monto"))["total"]
            or Decimal("0.00")
        )

        egresos_metodo = (
            movimientos
            .filter(
                tipo="egreso",
                metodo_pago=codigo,
            )
            .aggregate(total=Sum("monto"))["total"]
            or Decimal("0.00")
        )

        saldos_metodos.append(
            {
                "codigo": codigo,
                "nombre": nombre,
                "ingresos": ingresos_metodo,
                "egresos": egresos_metodo,
                "saldo": ingresos_metodo - egresos_metodo,
            }
        )

        contexto = {
            "ingresos": ingresos,
            "egresos": egresos,
            "saldo": saldo,
            "saldos_metodos": saldos_metodos,
            "ultimos_movimientos": movimientos[:5],
        }

    return render(
        request,
        "caja/dashboard.html",
        contexto,
    )


@login_required
def lista_movimientos(request):
    """
    Muestra el historial financiero del negocio.
    """

    movimientos = (
        MovimientoCaja.objects
        .filter(
            negocio=request.user.negocio,
        )
        .select_related(
            "usuario",
        )
    )

    return render(
        request,
        "caja/lista_movimientos.html",
        {
            "movimientos": movimientos,
        },
    )


@login_required
def crear_movimiento(request):
    """
    Registra manualmente un ingreso o egreso de caja.

    Los movimientos automáticos producidos por ventas,
    compras y abonos se procesarán desde sus servicios.
    """

    if request.method == "POST":

        formulario = MovimientoCajaForm(
            request.POST,
        )

        if formulario.is_valid():

            movimiento = registrar_movimiento(
                negocio=request.user.negocio,
                usuario=request.user,
                tipo=formulario.cleaned_data["tipo"],
                monto=formulario.cleaned_data["monto"],
                metodo_pago=formulario.cleaned_data[
                    "metodo_pago"
                ],
                concepto=formulario.cleaned_data[
                    "concepto"
                ],
                origen="manual",
                referencia=formulario.cleaned_data.get(
                    "referencia",
                    "",
                ),
                notas=formulario.cleaned_data.get(
                    "notas",
                    "",
                ),
            )

            messages.success(
                request,
                (
                    f"Movimiento #{movimiento.id} "
                    "registrado correctamente."
                ),
            )

            return redirect(
                "caja:dashboard"
            )

    else:

        formulario = MovimientoCajaForm()

    return render(
        request,
        "caja/crear_movimiento.html",
        {
            "formulario": formulario,
        },
    )