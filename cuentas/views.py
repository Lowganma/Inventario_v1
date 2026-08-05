from django.shortcuts import render,redirect, get_object_or_404
from django.db.models import Sum, Q


from .models import CuentaPorCobrar
from .forms import CuentaPorCobrarForm, AbonoForm
from clientes.models import Cliente

# Create your views here.

def dashboard(request):
    clientes_registrados = Cliente.objects.count()

    cuentas_pendientes = CuentaPorCobrar.objects.filter(
        estado="pendiente"
    ).count()

    cuentas_pagadas = CuentaPorCobrar.objects.filter(
        estado="pagada"
    ).count()

    cuentas = CuentaPorCobrar.objects.all()

    total_por_cobrar = sum(
        cuenta.saldo_pendiente
        for cuenta in cuentas
    )

    busqueda = request.GET.get("buscar", "").strip()

    resultados = CuentaPorCobrar.objects.none()

    if busqueda:
        resultados = CuentaPorCobrar.objects.filter(
            Q(cliente__nombre__icontains=busqueda)
            | Q(cliente__apellido__icontains=busqueda)
            | Q(cliente__telefono__icontains=busqueda)
            | Q(concepto__icontains=busqueda)
        ).select_related("cliente")

    contexto = {
        "clientes_registrados": clientes_registrados,
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
    

def lista_cuentas(request):
    busqueda = request.GET.get("buscar", "").strip()
    estado = request.GET.get("estado", "todas")
    orden = request.GET.get("orden", "desc")

    cuentas = CuentaPorCobrar.objects.select_related(
        "cliente"
    )

    if busqueda:
        cuentas = cuentas.filter(
            Q(cliente__nombre__icontains=busqueda)
            | Q(cliente__apellido__icontains=busqueda)
            | Q(cliente__telefono__icontains=busqueda)
            | Q(concepto__icontains=busqueda)
        )

    if estado == "pendiente":
        cuentas = cuentas.filter(estado="pendiente")

    elif estado == "pagada":
        cuentas = cuentas.filter(estado="pagada")

    if orden == "asc":
        cuentas = cuentas.order_by("fecha", "id")
    else:
        cuentas = cuentas.order_by("-fecha", "-id")

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

def crear_cuenta(request):
    if request.method == "POST":
        formulario = CuentaPorCobrarForm(request.POST)

        if formulario.is_valid():
            formulario.save()
            return redirect("cuentas:lista")

    else:
        formulario = CuentaPorCobrarForm()

    contexto = {
        "formulario": formulario,
    }

    return render(
        request,
        "cuentas/crear_cuenta.html",
        contexto,
    )

def detalle_cuenta(request, cuenta_id):
    cuenta = get_object_or_404(
        CuentaPorCobrar,
        id=cuenta_id,
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

def pagar_cuenta_completa(request, cuenta_id):
    cuenta = get_object_or_404(
        CuentaPorCobrar,
        id=cuenta_id,
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