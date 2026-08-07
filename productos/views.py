from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from . models import Categoria, Producto
from . forms import ProductoForm

# Create your views here.

# /productos

@login_required
def index(request):
    productos = Producto.objects.all()

    return render(
        request,
        "productos/index.html",
        context={
            "productos": productos
        }
    )

@login_required
def detalle(request, producto_id):
        producto = get_object_or_404(Producto, id=producto_id)

        return render(
            request,
            "productos/detalle.html",
            context={"producto": producto})

@login_required
def formulario(request):
        if request.method == "POST":
            form = ProductoForm(request.POST)
            if form.is_valid():
                  form.save()
                  return HttpResponseRedirect("/productos/")
        else:
            form = ProductoForm()

        return render(
            request,
            "productos/producto_form.html",
            {"form": form}
      )
