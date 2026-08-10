from django.shortcuts import redirect,render, get_object_or_404
from django.db.models import Q
from django.contrib.auth.decorators import login_required

from .forms import ClienteForm
from .models import Cliente
from decimal import Decimal
from usuarios.permisos import dueno_required

# Create your views here.

@login_required
def lista_clientes(request):
    """
    Muestra únicamente los clientes pertenecientes al negocio
    del usuario que tiene la sesión iniciada.
    """

    # Obtiene el texto escrito en el buscador.
    busqueda = request.GET.get("buscar", "").strip()

    # Conserva el modo de visualización seleccionado.
    vista = request.GET.get("vista", "tarjetas")

    # FILTRO PRINCIPAL:
    # solo trae clientes del negocio del usuario actual.
    clientes = Cliente.objects.filter(negocio=request.user.negocio)

    # Busca por nombre, apellido o teléfono.
    if busqueda:
        clientes = clientes.filter(
            Q(nombre__icontains=busqueda)
            | Q(apellido__icontains=busqueda)
            | Q(telefono__icontains=busqueda)
        )

    # Organiza alfabéticamente los resultados.
    clientes = clientes.order_by(
        "nombre",
        "apellido",
    )

    # Calcula las cuentas y el saldo de cada cliente.
    for cliente in clientes:

        # Solo tomamos en cuenta las cuentas que siguen pendientes.
        cuentas_pendientes = cliente.cuentas.filter(
            estado="pendiente"
        )

        # Cantidad real de cuentas pendientes del cliente.
        cliente.total_cuentas = (
            cuentas_pendientes.count()
        )

        # Saldo total pendiente, excluyendo cuentas pagadas y anuladas.
        cliente.total_pendiente = sum(
            (
                cuenta.saldo_pendiente
                for cuenta in cuentas_pendientes
            ),
            Decimal("0.00"),
        )

    contexto = {
        "clientes": clientes,
        "busqueda": busqueda,
        "vista_seleccionada": vista,
    }

    return render(
        request,
        "clientes/lista_clientes.html",
        contexto,
    )

@login_required
def crear_cliente(request):
    if request.method == "POST":
        formulario = ClienteForm(request.POST)

        if formulario.is_valid():
            cliente = formulario.save(commit=False)

            # El cliente queda asociado al negocio del usuario actual.
            cliente.negocio = request.user.negocio

            cliente.save()

            return redirect("clientes:lista")

    else:
        formulario = ClienteForm()

    contexto = {
        "formulario": formulario,
    }

    return render(
        request,
        "clientes/crear_cliente.html",
        contexto,
    )

@login_required
def editar_cliente(request, cliente_id):
    cliente = get_object_or_404(
        Cliente, id=cliente_id, negocio=request.user.negocio
    )

    if request.method == "POST":
        formulario = ClienteForm(
            request.POST,
            instance=cliente
        )

        if formulario.is_valid():
            formulario.save()
            return redirect('clientes:lista')

    else: 
        formulario = ClienteForm(instance=cliente)

    contexto = {
        'formulario': formulario,
        'cliente': cliente
    }

    return render(
        request,
        'clientes/editar_cliente.html',
        contexto
    )

@login_required
@dueno_required
def eliminar_cliente(request, cliente_id):
    cliente = get_object_or_404(
        Cliente, id=cliente_id, negocio=request.user.negocio
    )

    if request.method == "POST":
        cliente.delete()
        return redirect('clientes:lista')

    contexto = {
        'cliente': cliente
    }

    return render(
        request,
        'clientes/eliminar_cliente.html',
        contexto
    )
