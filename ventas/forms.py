from decimal import Decimal

from django import forms
from django.forms import formset_factory

from clientes.models import Cliente
from productos.models import (Producto, PresentacionProducto)

from .models import Venta


# ============================================================
# DATOS GENERALES DE LA VENTA
# ============================================================

class VentaForm(forms.ModelForm):
    """
    Datos generales de una venta.

    El negocio, usuario, totales y cuenta por cobrar
    se controlan desde el backend.
    """

    class Meta:
        model = Venta

        fields = [
            "cliente",
            "tipo_pago",
            "metodo_pago",
            "descuento",
            "notas",
        ]

        widgets = {
            "cliente": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "tipo_pago": forms.RadioSelect(),

            "metodo_pago": forms.Select(
                attrs = {
                    "class": "form-select",
                }
            ),

            "descuento": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "0.00",
                }
            ),

            "notas": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Observaciones opcionales",
                }
            ),
        }

    def __init__(self, *args, negocio=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Un negocio solamente puede vender a sus propios clientes.
        if negocio:
            self.fields["cliente"].queryset = (
                Cliente.objects.filter(
                    negocio=negocio,
                    estado="Activo",
                )
                .order_by("nombre", "apellido")
            )
        else:
            self.fields["cliente"].queryset = Cliente.objects.none()

        self.fields["cliente"].required = False

        self.fields["descuento"].required = False
        self.fields["descuento"].initial = Decimal("0.00")

    def clean(self):
        """
        Una venta fiada necesita obligatoriamente un cliente.
        """

        cleaned_data = super().clean()

        tipo_pago = cleaned_data.get("tipo_pago")
        metodo_pago = cleaned_data.get("metodo_pago")
        cliente = cleaned_data.get("cliente")

        if cleaned_data.get("descuento") is None:
         cleaned_data["descuento"] = Decimal("0.00")

        if tipo_pago == "fiado" and not cliente:
            self.add_error(
                "cliente",
                "Debes seleccionar un cliente para registrar una venta fiada.",
            )

        if tipo_pago != "fiado" and not metodo_pago:
            self.add_error(
                "metodo_pago",
                "Selecciona el método de pago",
            )

        if tipo_pago == "fiado":
            cleaned_data["metodo_pago"]=""


        return cleaned_data

    # ============================================================
# PRODUCTOS DE LA VENTA
# ============================================================

class DetalleVentaForm(forms.Form):
    """
    Representa un producto incluido en una venta.
    """

    producto = forms.ModelChoiceField(
        queryset=Producto.objects.none(),
        label="Producto",
        widget=forms.Select(
            attrs={
                "class": "form-select venta-producto",
            }
        ),
    )

    presentacion = forms.ModelChoiceField(
        queryset=PresentacionProducto.objects.none(),
        required=False,
        label="Presentación",
        widget=forms.Select(
            attrs={
                "class": "form-select venta-presentacion",
            }
        ),
    )

    cantidad = forms.IntegerField(
        min_value=1,
        initial=1,
        label="Cantidad",
        widget=forms.NumberInput(
            attrs={
                "class": "form-control venta-cantidad",
                "min": 1,
            }
        ),
    )

    precio_unitario = forms.DecimalField(
        min_value=Decimal("0.00"),
        max_digits=12,
        decimal_places=2,
        label="Precio",
        widget=forms.NumberInput(
            attrs={
                "class": "form-control venta-precio",
                "step": "0.01",
                "min": "0",
            }
        ),
    )

    def __init__(self, *args, negocio=None, **kwargs):
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


DetalleVentaFormSet = formset_factory(
    DetalleVentaForm,
    extra=1,
    can_delete=True,
)