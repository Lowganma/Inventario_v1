from django.shortcuts import render,redirect, get_object_or_404
from django.db.models import Sum, Q
from django.contrib.auth.decorators import login_required

from .models import CuentaPorCobrar
from .forms import CuentaPorCobrarForm, AbonoForm
from clientes.models import Cliente

# Create your views here.

@login_required
def dashboard(request):
    """
    Muestra únicamente los indicadores, cuentas y clientes
    pertenecientes al negocio del usuario autenticado.
    """

    # Protege a usuarios antiguos que todavía no tengan negocio.
    if not hasattr(request.user, "negocio"):
        return redirect("usuarios:registro")

    negocio = request.user.negocio

    # Clientes exclusivos del negocio actual.
    clientes = Cliente.objects.filter(
        negocio=negocio
    )

    # Cuentas cuyos clientes pertenecen al negocio actual.
    cuentas = CuentaPorCobrar.objects.filter(
        cliente__negocio=negocio
    ).select_related("cliente")

    # Indicadores del dashboard.
    total_clientes = clientes.count()

    cuentas_pendientes = cuentas.filter(
        estado="pendiente"
    ).count()

    cuentas_pagadas = cuentas.filter(
        estado="pagada"
    ).count()

    total_por_cobrar = sum(
        cuenta.saldo_pendiente
        for cuenta in cuentas
    )

    # Búsqueda del dashboard.
    busqueda = request.GET.get("buscar", "").strip()

    resultados = None

    if busqueda:
        resultados = cuentas.filter(
            Q(cliente__nombre__icontains=busqueda)
            | Q(cliente__apellido__icontains=busqueda)
            | Q(cliente__telefono__icontains=busqueda)
            | Q(concepto__icontains=busqueda)
        ).order_by(
            "-fecha",
            "-id",
        )

    contexto = {
        "total_clientes": total_clientes,
        "cuentas_pendientes": cuentas_pendientes,
        "cuentas_pagadas": cuentas_pagadas,
        "total_por_cobrar": total_por_cobrar,
        "busqueda": busqueda,
        "resultados": resultados,
    }

    return render(
        request,
        "cuentas/dashboard.html",
        contexto,
    )

@login_required
def lista_cuentas(request):
    """
    Muestra únicamente las cuentas pertenecientes al negocio
    del usuario autenticado.
    """

    # Texto ingresado en el buscador.
    busqueda = request.GET.get("buscar", "").strip()

    # Filtro por estado: todas, pendiente o pagada.
    estado = request.GET.get("estado", "todas")

    # Orden cronológico.
    orden = request.GET.get("orden", "desc")

    # FILTRO PRINCIPAL:
    # solo trae cuentas cuyos clientes pertenecen
    # al negocio del usuario actual.
    cuentas = CuentaPorCobrar.objects.select_related(
        "cliente"
    ).filter(
        cliente__negocio=request.user.negocio
    )

    # Búsqueda por datos del cliente o concepto.
    if busqueda:
        cuentas = cuentas.filter(
            Q(cliente__nombre__icontains=busqueda)
            | Q(cliente__apellido__icontains=busqueda)
            | Q(cliente__telefono__icontains=busqueda)
            | Q(concepto__icontains=busqueda)
        )

    # Filtro por estado.
    if estado == "pendiente":
        cuentas = cuentas.filter(
            estado="pendiente"
        )

    elif estado == "pagada":
        cuentas = cuentas.filter(
            estado="pagada"
        )

    # Orden ascendente o descendente.
    if orden == "asc":
        cuentas = cuentas.order_by(
            "fecha",
            "id",
        )
    else:
        cuentas = cuentas.order_by(
            "-fecha",
            "-id",
        )

    contexto = {
        "cuentas": cuentas,
        "busqueda": busqueda,
        "estado_seleccionado": estado,
        "orden_seleccionado": orden,
    }

    return render(
        request,
        "cuentas/lista_cuentas.html",
        contexto,
    )

@login_required
def crear_cuenta(request):
    """
    Crea una cuenta por cobrar y redirige a su detalle.

    La redirección evita que el navegador vuelva a enviar
    el formulario al actualizar la página.
    """

    if request.method == "POST":
        formulario = CuentaPorCobrarForm(request.POST)
    else:
        formulario = CuentaPorCobrarForm()

    # Solo muestra clientes pertenecientes al negocio actual.
    formulario.fields["cliente"].queryset = (
        request.user.negocio.clientes.all()
        .order_by("nombre", "apellido")
    )

    if request.method == "POST" and formulario.is_valid():
        cuenta = formulario.save(commit=False)

        # Evita asociar una cuenta con clientes de otro negocio.
        if cuenta.cliente.negocio_id != request.user.negocio.id:
            return redirect("cuentas:lista")

        cuenta.save()

        # Después de guardar, abandona el formulario
        # y muestra el detalle de la cuenta recién creada.
        return redirect(
            "cuentas:detalle",
            cuenta_id=cuenta.id,
        )

    contexto = {
        "formulario": formulario,
    }

    return render(
        request,
        "cuentas/crear_cuenta.html",
        contexto,
    )


@login_required
def detalle_cuenta(request, cuenta_id):
    cuenta = get_object_or_404(
        CuentaPorCobrar,
        id=cuenta_id,
        cliente__negocio=request.user.negocio
    )

    abonos = cuenta.abonos.all().order_by("-fecha_pago")

    contexto = {
        "cuenta": cuenta,
        "abonos": abonos,
    }

    return render(
        request,
        "cuentas/detalle_cuenta.html",
        contexto,
    )

@login_required
def registrar_abono(request, cuenta_id):
    cuenta = get_object_or_404(
        CuentaPorCobrar,
        id=cuenta_id,
    )

    if request.method == "POST":
        formulario = AbonoForm(
            request.POST,
            cuenta=cuenta,)

        if formulario.is_valid():
            abono = formulario.save(commit=False)
            abono.cuenta = cuenta
            abono.save()

            cuenta.refresh_from_db()
            if cuenta.saldo_pendiente <= 0:
                cuenta.estado = "pagada"
            else:
                cuenta.estado = "pendiente"

            cuenta.save(update_fields=["estado"])
            
            return redirect(
                "cuentas:detalle",
                cuenta_id=cuenta.id,
            )

    else:
        formulario = AbonoForm(cuenta=cuenta)

    contexto = {
        "cuenta": cuenta,
        "formulario": formulario,
    }

    return render(
        request,
        "cuentas/registrar_abono.html",
        contexto,
    )

@login_required
def pagar_cuenta_completa(request, cuenta_id):
    cuenta = get_object_or_404(
        CuentaPorCobrar,
        id=cuenta_id,
        cliente__negocio=request.user.negocio
    )

    if cuenta.saldo_pendiente <= 0:
        return redirect(
            "cuentas:detalle",
            cuenta_id=cuenta.id,
        )

    if request.method == "POST":
        formulario = AbonoForm(
            request.POST,
            cuenta=cuenta,
        )

        if formulario.is_valid():
            abono = formulario.save(commit=False)
            abono.cuenta = cuenta
            abono.save()

            cuenta.refresh_from_db()
            cuenta.estado = "pagada"
            cuenta.save(update_fields=["estado"])

            return redirect(
                "cuentas:detalle",
                cuenta_id=cuenta.id,
            )

    else:
        formulario = AbonoForm(
            cuenta=cuenta,
            initial={
                "monto_pagado": cuenta.saldo_pendiente,
            },
            )
    contexto = {
        "cuenta": cuenta,
        "formulario": formulario,
    }

    return render(
        request,
        "cuentas/pagar_cuenta_completa.html",
        contexto,
    )