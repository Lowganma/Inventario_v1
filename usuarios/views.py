from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from .forms import EmpleadoForm, ModulosNegocioForm, RegistroForm, RolUsuarioForm
from .models import MODULOS_DISPONIBLES, PerfilUsuario
from .permisos import admin_required
from .services import actualizar_modulos


def registro(request):
    """
    Registra al propietario, crea su negocio e inicia su sesión.
    """

    # Un usuario autenticado no necesita volver al registro.
    if request.user.is_authenticated:
        return redirect("inicio")

    if request.method == "POST":
        formulario = RegistroForm(request.POST)

        if formulario.is_valid():
            usuario = formulario.save()

            # Inicia sesión inmediatamente después del registro.
            login(request, usuario)

            return redirect("inicio")

    else:
        formulario = RegistroForm()

    contexto = {
        "formulario": formulario,
    }

    return render(
        request,
        "usuarios/registro.html",
        contexto,
    )


@login_required
@admin_required
def configurar_modulos(request):
    negocio = request.user.negocio
    actuales = set(negocio.modulos.filter(activo=True).values_list("modulo", flat=True))
    formulario = ModulosNegocioForm(request.POST or None, initial={"modulos": actuales})
    if request.method == "POST" and formulario.is_valid():
        try:
            actualizar_modulos(negocio=negocio, seleccionados=formulario.cleaned_data["modulos"])
        except ValidationError as error:
            formulario.add_error(None, error)
        else:
            messages.success(request, "Configuración de módulos actualizada.")
            return redirect("usuarios:modulos")
    return render(request, "usuarios/modulos.html", {"formulario": formulario, "catalogo": MODULOS_DISPONIBLES})


@login_required
@admin_required
def lista_usuarios(request):
    miembros = PerfilUsuario.objects.filter(negocio=request.user.negocio).select_related("usuario")
    return render(request, "usuarios/lista.html", {"miembros": miembros, "propietario": request.user.negocio.propietario})


@login_required
@admin_required
def crear_usuario(request):
    formulario = EmpleadoForm(request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        usuario = formulario.save()
        PerfilUsuario.objects.create(usuario=usuario, negocio=request.user.negocio, rol=formulario.cleaned_data["rol"])
        messages.success(request, "Usuario creado correctamente.")
        return redirect("usuarios:lista")
    return render(request, "usuarios/form_usuario.html", {"formulario": formulario})


@login_required
@admin_required
def editar_rol(request, perfil_id):
    # El filtro empresarial evita modificar miembros mediante identificadores ajenos.
    perfil = get_object_or_404(PerfilUsuario, id=perfil_id, negocio=request.user.negocio)
    formulario = RolUsuarioForm(request.POST or None, instance=perfil)
    if request.method == "POST" and formulario.is_valid():
        formulario.save()
        return redirect("usuarios:lista")
    return render(request, "usuarios/form_usuario.html", {"formulario": formulario, "perfil": perfil})
