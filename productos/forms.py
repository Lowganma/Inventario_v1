from django import forms
from django.db.models import Q

from .models import Categoria, Producto, PresentacionProducto


class CategoriaForm(forms.ModelForm):
    def __init__(self, *args, negocio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.negocio = negocio

    class Meta:
        model = Categoria
        fields = ["nombre", "descripcion", "color", "activa"]
        widgets = {
            "nombre": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ejemplo: Bebidas"}
            ),
            "descripcion": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Descripción opcional de la categoría",
                }
            ),
            "color": forms.TextInput(
                attrs={"class": "form-control form-control-color", "type": "color"}
            ),
            "activa": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_nombre(self):
        """Valida la unicidad dentro de la empresa antes de llegar a la base de datos."""
        nombre = self.cleaned_data["nombre"].strip()
        categorias = Categoria.objects.filter(negocio=self.negocio, nombre__iexact=nombre)
        if self.instance.pk:
            categorias = categorias.exclude(pk=self.instance.pk)
        if self.negocio and categorias.exists():
            raise forms.ValidationError("Ya existe una categoría con este nombre.")
        return nombre


class ProductoForm(forms.ModelForm):
    def __init__(self, *args, negocio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.negocio = negocio
        # La lista nunca expone categorías de otra empresa.
        categorias = Categoria.objects.none()
        if negocio:
            # Las altas solo ofrecen categorías activas. Al editar se conserva la
            # categoría actual aunque posteriormente haya sido desactivada.
            categorias = Categoria.objects.filter(negocio=negocio, activa=True)
            if self.instance.pk and self.instance.categoria_id:
                categorias = Categoria.objects.filter(negocio=negocio).filter(
                    Q(activa=True) | Q(pk=self.instance.categoria_id)
                )
        self.fields["categoria"].queryset = categorias

    class Meta:
        model = Producto
        fields = [
            "tipo",
            "categoria",
            "codigo",
            "nombre",
            "descripcion",
            "imagen",
            "unidad_base",
            "stock",
            "stock_minimo",
            "costo",
            "precio_venta",
            "activo",
        ]
        widgets = {
            "categoria": forms.Select(attrs={"class": "form-select"}),
            "codigo": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ejemplo: BEB-001"}
            ),
            "nombre": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ejemplo: Coca-Cola 2L"}
            ),
            "descripcion": forms.Textarea(
                attrs={"class": "form-control", "rows": 3, "placeholder": "Opcional"}
            ),
            "imagen": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/*",
                }
            ),
            "tipo": forms.RadioSelect(
                attrs={
                    "class": "btn-check",
                }
            ),

            "unidad_base": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "stock": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "stock_minimo": forms.NumberInput(
                attrs={"class": "form-control", "min": 0}
            ),
            "costo": forms.NumberInput(
                attrs={"class": "form-control", "min": 0, "step": "0.01"}
            ),
            "precio_venta": forms.NumberInput(
                attrs={"class": "form-control", "min": 0, "step": "0.01"}
            ),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "precio_venta": "Precio de venta", 
            "stock_minimo": "Stock mínimo",
            "tipo": "Tipo",
            "unidad_base": "Unidad de inventario",
            "precio_venta": "Precio de venta",
            "stock_minimo": "Stock mínimo",
            }
        help_texts = {
            "codigo": "Opcional. Si lo indicas, no podrá repetirse en tu negocio.",
             "unidad_base":"Unidad mínima en la que controlarás las existencias.",
            "stock_minimo": "Se avisará cuando el stock sea igual o menor a este valor.",
        }

    def clean_categoria(self):
        categoria = self.cleaned_data["categoria"]
        if not self.negocio or categoria.negocio_id != self.negocio.id:
            raise forms.ValidationError("Selecciona una categoría de tu negocio.")
        return categoria

    def clean_codigo(self):
        """Los códigos informados son únicos únicamente dentro del negocio."""
        codigo = self.cleaned_data["codigo"].strip()
        if not codigo or not self.negocio:
            return codigo
        productos = Producto.objects.filter(negocio=self.negocio, codigo=codigo)
        if self.instance.pk:
            productos = productos.exclude(pk=self.instance.pk)
        if productos.exists():
            raise forms.ValidationError("Ya existe un producto con este código.")
        return codigo

    def clean_nombre(self):
        nombre = self.cleaned_data["nombre"].strip()

        if not self.negocio:
            return nombre

        productos = Producto.objects.filter(
            negocio=self.negocio,
            nombre__iexact=nombre,
        )

        if self.instance.pk:
            productos = productos.exclude(
                pk=self.instance.pk
            )

        if productos.exists():
            raise forms.ValidationError(
                "Ya existe un producto con este nombre."
            )

        return nombre


class PresentacionProductoForm(forms.ModelForm):

    class Meta:
        model = PresentacionProducto

        fields = [
            "nombre",
            "cantidad_unidades",
            "precio_venta",
        ]

        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ejemplo: Docena, Resma, Caja x24",
                }
            ),

            "cantidad_unidades": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0.001",
                    "step": "0.001",
                }
            ),

            "precio_venta": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "step": "0.01",
                    "placeholder": "Opcional",
                }
            ),
        }

        labels = {
            "nombre": "Nombre",
            "cantidad_unidades": "Contiene",
            "precio_venta": "Precio de venta",
        }