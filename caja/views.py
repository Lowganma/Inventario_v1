from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from usuarios.permisos import dueno_required

from .forms import AbrirCajaForm, CerrarCajaForm, MovimientoCajaForm
from .models import CajaDiaria, MovimientoCaja
from .services.caja import abrir_caja, cerrar_caja, obtener_resumen_caja, registrar_movimiento


@login_required
def dashboard_caja(request):
    caja = CajaDiaria.objects.filter(negocio=request.user.negocio, fecha=timezone.localdate()).first()
    resumen = obtener_resumen_caja(caja) if caja else None
    return render(request, "caja/dashboard.html", {"caja": caja, "resumen": resumen})


@login_required
def abrir_caja_view(request):
    formulario = AbrirCajaForm(request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        try:
            abrir_caja(negocio=request.user.negocio, usuario=request.user, **formulario.cleaned_data)
        except ValidationError as error:
            formulario.add_error(None, error)
        else:
            messages.success(request, "Caja abierta correctamente.")
            return redirect("caja:dashboard")
    return render(request, "caja/abrir_caja.html", {"formulario": formulario})


@login_required
@dueno_required
def cerrar_caja_view(request):
    caja = get_object_or_404(CajaDiaria, negocio=request.user.negocio, fecha=timezone.localdate(), estado="abierta")
    resumen = obtener_resumen_caja(caja)
    formulario = CerrarCajaForm(request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        try:
            cerrar_caja(caja=caja, usuario=request.user, **formulario.cleaned_data)
        except ValidationError as error:
            formulario.add_error(None, error)
        else:
            messages.success(request, "Caja cerrada correctamente.")
            return redirect("caja:detalle_cierre", caja_id=caja.id)
    return render(request, "caja/cerrar_caja.html", {"caja": caja, "resumen": resumen, "formulario": formulario})


@login_required
@dueno_required
def lista_cierres(request):
    cajas = CajaDiaria.objects.filter(negocio=request.user.negocio)
    filas = [{"caja": caja, "resumen": obtener_resumen_caja(caja)} for caja in cajas]
    return render(request, "caja/lista_cierres.html", {"filas": filas})


@login_required
@dueno_required
def detalle_cierre(request, caja_id):
    caja = get_object_or_404(CajaDiaria, id=caja_id, negocio=request.user.negocio)
    return render(request, "caja/detalle_cierre.html", {"caja": caja, "resumen": obtener_resumen_caja(caja)})


@login_required
def lista_movimientos(request):
    movimientos = MovimientoCaja.objects.filter(negocio=request.user.negocio).select_related("usuario")
    return render(request, "caja/lista_movimientos.html", {"movimientos": movimientos})


@login_required
def crear_movimiento(request):
    caja = CajaDiaria.objects.filter(negocio=request.user.negocio, fecha=timezone.localdate(), estado="abierta").first()
    if caja is None:
        messages.error(request, "Debes abrir la caja de hoy; una caja cerrada no admite movimientos.")
        return redirect("caja:dashboard")
    formulario = MovimientoCajaForm(request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        try:
            movimiento = registrar_movimiento(negocio=request.user.negocio, usuario=request.user, origen="manual", **formulario.cleaned_data)
        except ValidationError as error:
            formulario.add_error(None, error)
        else:
            messages.success(request, f"Movimiento #{movimiento.id} registrado correctamente.")
            return redirect("caja:dashboard")
    return render(request, "caja/crear_movimiento.html", {"formulario": formulario})
