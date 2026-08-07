from decimal import Decimal

from django import forms
from django.forms import formset_factory

from productos.models import Producto

from .models import Compra


# ============================================================
# FORMULARIO GENERAL DE LA COMPRA
# ============================================================

class CompraForm(forms.ModelForm):
    """
    Formulario con los datos generales de una compra.

    El negocio, el usuario, la fecha y el total NO son
    seleccionados manualmente por el usuario.
    Esos valores son controlados por el backend.
    """

    class Meta:
        model = Compra

        fields = [
            "metodo_pago",
            "notas",
        ]

        widgets = {
            "notas": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": (
                        "Observaciones opcionales sobre esta compra"
                    ),
                }
            ),
            "metodo_pago": forms.Select(
                attrs={
                    "class": "form-select",
                }
),
        }

        


# ============================================================
# FORMULARIO PARA CADA PRODUCTO DE LA COMPRA
# ============================================================

class DetalleCompraForm(forms.Form):
    """
    Representa una línea dentro de la compra.

    Ejemplo:
    Coca-Cola | 10 | $1.20 | $2.00
    """

    producto = forms.ModelChoiceField(
        queryset=Producto.objects.none(),
        label="Producto",
        widget=forms.Select(
            attrs={
                "class": "form-select compra-producto",
            }
        ),
    )

    cantidad = forms.IntegerField(
        min_value=1,
        initial=1,
        label="Cantidad",
        widget=forms.NumberInput(
            attrs={
                "class": "form-control compra-cantidad",
                "min": 1,
                "placeholder": "Cantidad",
            }
        ),
    )

    precio_compra = forms.DecimalField(
        min_value=Decimal("0.00"),
        max_digits=12,
        decimal_places=2,
        label="Precio de compra",
        widget=forms.NumberInput(
            attrs={
                "class": "form-control compra-precio",
                "step": "0.01",
                "min": "0",
                "placeholder": "0.00",
            }
        ),
    )

    precio_venta = forms.DecimalField(
        min_value=Decimal("0.00"),
        max_digits=12,
        decimal_places=2,
        label="Precio de venta",
        widget=forms.NumberInput(
            attrs={
                "class": "form-control venta-precio",
                "step": "0.01",
                "min": "0",
                "placeholder": "0.00",
            }
        ),
    )

    def __init__(self, *args, negocio=None, **kwargs):
        """
        Limita la lista de productos al negocio autenticado.

        Esto evita que un usuario pueda seleccionar productos
        pertenecientes a otro negocio.
        """

        super().__init__(*args, **kwargs)

        if negocio:
            self.fields["producto"].queryset = (
                Producto.objects.filter(
                    negocio=negocio,
                    activo=True,
                )
                .select_related("categoria")
                .order_by("nombre")
            )


# ============================================================
# FORMSET DE PRODUCTOS
# ============================================================

DetalleCompraFormSet = formset_factory(
    DetalleCompraForm,
    extra=1,
    can_delete=True,
)