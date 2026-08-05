from django.shortcuts import redirect,render, get_object_or_404
from django.db.models import Q

from .forms import ClienteForm
from .models import Cliente

# Create your views here.

def lista_clientes(request):
    # Texto ingresado en el buscador.
    busqueda = request.GET.get("buscar", "").strip()

    # Tipo de visualización seleccionada.
    # Puede ser "tarjetas" o "lista".
    vista = request.GET.get("vista", "tarjetas")

    # Consulta inicial de todos los clientes.
    clientes = Cliente.objects.all()

    # Filtra por nombre, apellido o teléfono.
    if busqueda:
        clientes = clientes.filter(
            Q(nombre__icontains=busqueda)
            | Q(apellido__icontains=busqueda)
            | Q(telefono__icontains=busqueda)
        )

    # Orden alfabético.
    clientes = clientes.order_by("nombre", "apellido")

    # Calcula los datos financieros de cada cliente.
    for cliente in clientes:
        cuentas = cliente.cuentas.all()

        cliente.total_cuentas = cuentas.count()

        cliente.total_pendiente = sum(
            cuenta.saldo_pendiente
            for cuenta in cuentas
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
    clientes = Cliente.objects.all()

    for cliente in clientes:
        cuentas = cliente.cuentas.all()

        cliente.total_cuentas = cuentas.count()

        cliente.total_pendiente = sum(
            cuenta.saldo_pendiente
            for cuenta in cuentas
        )

    contexto = {
        "clientes": clientes,
    }

    return render(
        request,
        "clientes/lista_clientes.html",
        contexto,
    )

def crear_cliente(request):
    if request.method == "POST":
        formulario = ClienteForm(request.POST)

        if formulario.is_valid():
            formulario.save()
            return redirect('clientes:lista')
    else:
        formulario = ClienteForm()

    contexto = {
        'formulario': formulario
    }

    return render(
        request,
        'clientes/crear_cliente.html',
        contexto
    )

def editar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)

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

def eliminar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)

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
