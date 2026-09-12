from decimal import Decimal

from django import forms
from django.forms import formset_factory

from clientes.models import Cliente
from productos.models import Producto, PresentacionProducto

from .models import Venta


class VentaForm(forms.ModelForm):
    aplicar_descuento = forms.BooleanField(required=False, label="Aplicar descuento")
    tipo_descuento = forms.ChoiceField(
        required=False,
        choices=[("", "---------")] + Venta.TIPOS_DESCUENTO,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Tipo de descuento",
    )
    valor_descuento = forms.DecimalField(
        required=False,
        min_value=Decimal("0.00"),
        max_digits=12,
        decimal_places=2,
        initial=Decimal("0.00"),
        widget=forms.NumberInput(
            attrs={"class": "form-control", "step": "0.01", "min": "0", "placeholder": "0.00"}
        ),
        label="Valor del descuento",
    )

    class Meta:
        model = Venta
        fields = [
            "cliente",
            "tipo_pago",
            "metodo_pago",
            "referencia_pago",
            "detalle_pago",
            "notas",
        ]
        widgets = {
            "cliente": forms.Select(attrs={"class": "form-select"}),
            "tipo_pago": forms.RadioSelect(),
            "metodo_pago": forms.Select(attrs={"class": "form-select"}),
            "referencia_pago": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Número o referencia de la transferencia"}
            ),
            "detalle_pago": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Describe el método de pago"}
            ),
            "notas": forms.Textarea(
                attrs={"class": "form-control", "rows": 3, "placeholder": "Observaciones opcionales"}
            ),
        }

    def __init__(self, *args, negocio=None, **kwargs):
        super().__init__(*args, **kwargs)

        if negocio:
            self.fields["cliente"].queryset = (
                Cliente.objects.filter(negocio=negocio, estado="Activo")
                .order_by("nombre", "apellido")
            )
        else:
            self.fields["cliente"].queryset = Cliente.objects.none()

        self.fields["cliente"].required = False
        self.fields["referencia_pago"].required = False
        self.fields["detalle_pago"].required = False
        self.fields["notas"].required = False

    def clean(self):
        cleaned_data = super().clean()

        tipo_pago = cleaned_data.get("tipo_pago")
        metodo_pago = cleaned_data.get("metodo_pago")
        cliente = cleaned_data.get("cliente")
        referencia_pago = (cleaned_data.get("referencia_pago") or "").strip()
        detalle_pago = (cleaned_data.get("detalle_pago") or "").strip()
        aplicar_descuento = cleaned_data.get("aplicar_descuento")
        tipo_descuento = cleaned_data.get("tipo_descuento") or ""
        valor_descuento = cleaned_data.get("valor_descuento") or Decimal("0.00")

        if tipo_pago == "fiado":
            if not cliente:
                self.add_error("cliente", "Debes seleccionar un cliente para registrar una venta fiada.")
            cleaned_data["metodo_pago"] = ""
            cleaned_data["referencia_pago"] = ""
            cleaned_data["detalle_pago"] = ""
        else:
            if not metodo_pago:
                self.add_error("metodo_pago", "Selecciona el método de pago.")

            if metodo_pago == "transferencia" and not referencia_pago:
                self.add_error("referencia_pago", "Ingresa la referencia de la transferencia.")

            if metodo_pago == "otro" and not detalle_pago:
                self.add_error("detalle_pago", "Describe el método de pago utilizado.")

            if metodo_pago != "transferencia":
                cleaned_data["referencia_pago"] = ""
            if metodo_pago != "otro":
                cleaned_data["detalle_pago"] = ""

        if aplicar_descuento:
            if not tipo_descuento:
                self.add_error("tipo_descuento", "Selecciona el tipo de descuento.")
            if valor_descuento <= 0:
                self.add_error("valor_descuento", "El descuento debe ser mayor que cero.")
            if tipo_descuento == "porcentaje" and valor_descuento > 100:
                self.add_error("valor_descuento", "El porcentaje no puede superar 100%.")
        else:
            cleaned_data["tipo_descuento"] = ""
            cleaned_data["valor_descuento"] = Decimal("0.00")

        return cleaned_data


class DetalleVentaForm(forms.Form):
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.none(),
        label="Producto o servicio",
        widget=forms.Select(attrs={"class": "form-select venta-producto"}),
    )
    presentacion = forms.ModelChoiceField(
        queryset=PresentacionProducto.objects.none(),
        required=False,
        label="Presentación",
        widget=forms.Select(attrs={"class": "form-select venta-presentacion"}),
    )
    cantidad = forms.DecimalField(
        min_value=Decimal("0.01"),
        max_digits=12,
        decimal_places=2,
        initial=Decimal("1.00"),
        label="Cantidad",
        widget=forms.NumberInput(
            attrs={"class": "form-control venta-cantidad", "min": "0.01", "step": "0.01"}
        ),
    )
    precio_unitario = forms.DecimalField(
        required=False,
        min_value=Decimal("0.00"),
        max_digits=12,
        decimal_places=2,
        label="Precio",
        widget=forms.NumberInput(
            attrs={
                "class": "form-control venta-precio",
                "step": "0.01",
                "min": "0",
                "readonly": "readonly",
            }
        ),
    )

    def __init__(self, *args, negocio=None, **kwargs):
        super().__init__(*args, **kwargs)

        if negocio:
            self.fields["producto"].queryset = (
                Producto.objects.filter(negocio=negocio, activo=True)
                .select_related("categoria")
                .order_by("nombre")
            )
            self.fields["presentacion"].queryset = (
                PresentacionProducto.objects.filter(
                    producto__negocio=negocio,
                    producto__activo=True,
                    activa=True,
                )
                .select_related("producto")
                .order_by("producto__nombre", "cantidad_unidades")
            )
        else:
            self.fields["producto"].queryset = Producto.objects.none()
            self.fields["presentacion"].queryset = PresentacionProducto.objects.none()

    def clean(self):
        cleaned_data = super().clean()

        producto = cleaned_data.get("producto")
        presentacion = cleaned_data.get("presentacion")
        cantidad = cleaned_data.get("cantidad")

        if not producto or cantidad is None:
            return cleaned_data

        if presentacion and presentacion.producto_id != producto.id:
            self.add_error("presentacion", "La presentación seleccionada no pertenece a este producto.")
            return cleaned_data

        if producto.tipo == "servicio":
            cleaned_data["presentacion"] = None
            return cleaned_data

        if producto.unidad_base == "unidad" and cantidad != cantidad.to_integral_value():
            self.add_error("cantidad", "La cantidad debe ser un número entero para productos por unidad.")

        if (
            presentacion
            and Decimal(presentacion.cantidad_unidades) != Decimal("1")
            and cantidad != cantidad.to_integral_value()
        ):
            self.add_error("cantidad", "La cantidad de presentaciones debe ser un número entero.")

        return cleaned_data


DetalleVentaFormSet = formset_factory(
    DetalleVentaForm,
    extra=0,
    can_delete=True,
)
