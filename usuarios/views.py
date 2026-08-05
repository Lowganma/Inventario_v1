from django.contrib.auth import login
from django.shortcuts import redirect, render

from .forms import RegistroForm


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