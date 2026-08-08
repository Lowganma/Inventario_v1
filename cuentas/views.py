from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import (
    DecimalField,
    ExpressionWrapper,
    F,
    Q,
    Sum,
)
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils import timezone

from caja.models import MovimientoCaja
from clientes.models import Cliente
from compras.models import Compra
from productos.models import Producto
from ventas.models import Venta

from .forms import AbonoForm, CuentaPorCobrarForm
from .models import CuentaPorCobrar, TasaCambio
from .services.cobros import registrar_abono_cuenta
# Create your views here.


@login_required
def dashboard(request):
    """
    Dashboard general del negocio.

    Consolida indicadores procedentes de clientes,
    cuentas por cobrar, ventas, compras, inventario
    y caja, sin trasladar lógica de negocio a esta vista.
    """

    # ========================================================
    # NEGOCIO ACTUAL
    # ========================================================

    # Conservamos compatibilidad con usuarios antiguos
    # que pudieran no tener todavía un negocio asociado.
    from usuarios.models import Negocio

    negocio, _ = Negocio.objects.get_or_create(
        propietario=request.user,
        defaults={
            "nombre": f"Negocio de {request.user.username}",
        },
    )

    hoy = timezone.localdate()

    # ========================================================
    # QUERYSETS BASE
    # ========================================================

    clientes = Cliente.objects.filter(
        negocio=negocio,
    )

    cuentas = (
        CuentaPorCobrar.objects
        .filter(
            cliente__negocio=negocio,
        )
        .select_related("cliente")
    )

    ventas = Venta.objects.filter(
        negocio=negocio,
    )

    compras = Compra.objects.filter(
        negocio=negocio,
    )

    productos = Producto.objects.filter(
        negocio=negocio,
        activo=True,
    )

    movimientos = MovimientoCaja.objects.filter(
        negocio=negocio,
    )

    # ========================================================
    # VENTAS DE HOY
    # ========================================================

    ventas_hoy = ventas.filter(
        fecha__date=hoy,
        estado="completada",
    )

    cantidad_ventas_hoy = ventas_hoy.count()

    total_ventas_hoy = (
        ventas_hoy.aggregate(
            total=Sum("total")
        )["total"]
        or Decimal("0.00")
    )

    unidades_vendidas_hoy = (
        ventas_hoy.aggregate(
            total=Sum("detalles__cantidad")
        )["total"]
        or 0
    )

    # Ventas fiadas realizadas hoy.
    ventas_fiadas_hoy = ventas_hoy.filter(
        tipo_pago="fiado",
    )

    total_fiado_hoy = (
        ventas_fiadas_hoy.aggregate(
            total=Sum("total")
        )["total"]
        or Decimal("0.00")
    )

    # ========================================================
    # COMPRAS DE HOY
    # ========================================================

    compras_hoy = compras.filter(
        fecha=hoy,
    )

    cantidad_compras_hoy = compras_hoy.count()

    total_compras_hoy = (
        compras_hoy.aggregate(
            total=Sum("total")
        )["total"]
        or Decimal("0.00")
    )

    # ========================================================
    # CAJA
    # ========================================================

    movimientos_hoy = movimientos.filter(
        fecha__date=hoy,
    )

    ingresos_hoy = (
        movimientos_hoy
        .filter(tipo="ingreso")
        .aggregate(total=Sum("monto"))["total"]
        or Decimal("0.00")
    )

    egresos_hoy = (
        movimientos_hoy
        .filter(tipo="egreso")
        .aggregate(total=Sum("monto"))["total"]
        or Decimal("0.00")
    )

    flujo_hoy = ingresos_hoy - egresos_hoy

    # Saldo acumulado registrado en Caja.
    ingresos_totales = (
        movimientos
        .filter(tipo="ingreso")
        .aggregate(total=Sum("monto"))["total"]
        or Decimal("0.00")
    )

    egresos_totales = (
        movimientos
        .filter(tipo="egreso")
        .aggregate(total=Sum("monto"))["total"]
        or Decimal("0.00")
    )

    saldo_caja = ingresos_totales - egresos_totales

    # Abonos recibidos específicamente hoy.
    abonos_hoy = (
        movimientos_hoy
        .filter(origen="abono")
        .aggregate(total=Sum("monto"))["total"]
        or Decimal("0.00")
    )

    # Cinco operaciones financieras más recientes.
    ultimos_movimientos = (
        movimientos
        .select_related("usuario")
        .order_by("-fecha", "-id")[:5]
    )

    # ========================================================
    # INVENTARIO
    # ========================================================

    total_productos = productos.count()

    unidades_inventario = (
        productos.aggregate(
            total=Sum("stock")
        )["total"]
        or 0
    )

    productos_agotados = productos.filter(
        stock=0,
    ).count()

    productos_stock_bajo = (
        productos
        .filter(
            stock__gt=0,
            stock__lte=F("stock_minimo"),
        )
        .count()
    )

    # Valor aproximado del inventario según costo.
    valor_linea = ExpressionWrapper(
        F("stock") * F("costo"),
        output_field=DecimalField(
            max_digits=14,
            decimal_places=2,
        ),
    )

    valor_inventario = (
        productos.aggregate(
            total=Sum(valor_linea)
        )["total"]
        or Decimal("0.00")
    )

    # ========================================================
    # CLIENTES Y CUENTAS POR COBRAR
    # ========================================================

    total_clientes = clientes.count()

    cuentas_pendientes_qs = cuentas.filter(
        estado="pendiente",
    )

    cuentas_pendientes = (
        cuentas_pendientes_qs.count()
    )

    cuentas_pagadas = cuentas.filter(
        estado="pagada",
    ).count()

    # Cuenta como vencida solamente si sigue pendiente
    # y posee una fecha de vencimiento anterior a hoy.
    cuentas_vencidas = (
        cuentas_pendientes_qs
        .filter(
            fecha_vencimiento__lt=hoy,
        )
        .count()
    )

    total_por_cobrar = sum(
        (
            cuenta.saldo_pendiente
            for cuenta in cuentas_pendientes_qs
        ),
        Decimal("0.00"),
    )

    # ========================================================
    # TASA BCV
    # ========================================================

    tasa_bcv = (
        TasaCambio.objects
        .filter(moneda="USD")
        .order_by(
            "-fecha_vigencia",
            "-id",
        )
        .first()
    )

    total_por_cobrar_bs = None

    if tasa_bcv:
        total_por_cobrar_bs = (
            total_por_cobrar
            * tasa_bcv.valor
        )

    # ========================================================
    # BÚSQUEDA DE CUENTAS
    # ========================================================

    busqueda = (
        request.GET
        .get("buscar", "")
        .strip()
    )

    resultados = None

    if busqueda:

        resultados = (
            cuentas
            .filter(
                Q(
                    cliente__nombre__icontains=busqueda
                )
                | Q(
                    cliente__apellido__icontains=busqueda
                )
                | Q(
                    cliente__telefono__icontains=busqueda
                )
                | Q(
                    concepto__icontains=busqueda
                )
            )
            .order_by(
                "-fecha",
                "-id",
            )
        )

    # ========================================================
    # CONTEXTO
    # ========================================================

    contexto = {
        # Fecha
        "hoy": hoy,

        # Ventas
        "cantidad_ventas_hoy": cantidad_ventas_hoy,
        "total_ventas_hoy": total_ventas_hoy,
        "unidades_vendidas_hoy": unidades_vendidas_hoy,
        "total_fiado_hoy": total_fiado_hoy,

        # Compras
        "cantidad_compras_hoy": cantidad_compras_hoy,
        "total_compras_hoy": total_compras_hoy,

        # Caja
        "ingresos_hoy": ingresos_hoy,
        "egresos_hoy": egresos_hoy,
        "flujo_hoy": flujo_hoy,
        "saldo_caja": saldo_caja,
        "abonos_hoy": abonos_hoy,
        "ultimos_movimientos": ultimos_movimientos,

        # Inventario
        "total_productos": total_productos,
        "unidades_inventario": unidades_inventario,
        "productos_stock_bajo": productos_stock_bajo,
        "productos_agotados": productos_agotados,
        "valor_inventario": valor_inventario,

        # Clientes
        "total_clientes": total_clientes,

        # Cuentas
        "cuentas_pendientes": cuentas_pendientes,
        "cuentas_pagadas": cuentas_pagadas,
        "cuentas_vencidas": cuentas_vencidas,
        "total_por_cobrar": total_por_cobrar,

        # BCV
        "tasa_bcv": tasa_bcv,
        "total_por_cobrar_bs": total_por_cobrar_bs,

        # Buscador
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
    
    venta_origen = getattr(
        cuenta, 
        "venta", 
        None
    )


    abonos = cuenta.abonos.all().order_by("-fecha_pago")

    contexto = {
        "cuenta": cuenta,
        "abonos": abonos,
        "venta_origen": venta_origen,
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
        cliente__negocio=request.user.negocio,
    )

    if request.method == "POST":

        formulario = AbonoForm(
            request.POST
        )

        if formulario.is_valid():

            try:

                registrar_abono_cuenta(
                    cuenta=cuenta,
                    usuario=request.user,

                    monto_pagado=formulario.cleaned_data[
                        "monto_pagado"
                    ],

                    fecha_pago=formulario.cleaned_data[
                        "fecha_pago"
                    ],

                    metodo=formulario.cleaned_data[
                        "metodo"
                    ],

                    referencia=formulario.cleaned_data.get(
                        "referencia",
                        "",
                    ),

                    notas=formulario.cleaned_data.get(
                        "notas",
                        "",
                    ),
                )

            except ValidationError as error:

                formulario.add_error(
                    "monto_pagado",
                    error.messages[0],
                )

            else:

                messages.success(
                    request,
                    "Abono registrado correctamente.",
                )

                return redirect(
                    "cuentas:detalle",
                    cuenta_id=cuenta.id,
                )

    else:

        formulario = AbonoForm()

    return render(
        request,
        "cuentas/registrar_abono.html",
        {
            "cuenta": cuenta,
            "formulario": formulario,
        },
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

            registrar_abono_cuenta(
                cuenta=cuenta,
                usuario=request.user,

                monto_pagado=formulario.cleaned_data[
                    "monto_pagado"
                ],

                fecha_pago=formulario.cleaned_data[
                    "fecha_pago"
                ],

                metodo=formulario.cleaned_data[
                    "metodo"
                ],

                referencia=formulario.cleaned_data.get(
                    "referencia",
                    "",
                ),

                notas=formulario.cleaned_data.get(
                    "notas",
                    "",
                ),
            )

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
