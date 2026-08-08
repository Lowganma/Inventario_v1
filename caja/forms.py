from django import forms

from .models import MovimientoCaja


class AbrirCajaForm(forms.Form):
    saldo_inicial = forms.DecimalField(min_value=0, max_digits=12, decimal_places=2, widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}))
    notas = forms.CharField(required=False, widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}))


class CerrarCajaForm(forms.Form):
    saldo_final_declarado = forms.DecimalField(min_value=0, max_digits=12, decimal_places=2, widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}))
    notas = forms.CharField(required=False, widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}))


class MovimientoCajaForm(forms.ModelForm):
    """
    Formulario destinado exclusivamente a movimientos
    manuales de caja.

    Los movimientos originados por ventas, compras o abonos
    serán generados automáticamente por sus respectivos
    servicios y no mediante este formulario.
    """

    class Meta:
        model = MovimientoCaja

        fields = [
            "tipo",
            "monto",
            "metodo_pago",
            "concepto",
            "referencia",
            "notas",
        ]

        widgets = {
            "tipo": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "monto": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0.01",
                    "placeholder": "0.00",
                }
            ),

            "metodo_pago": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "concepto": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ejemplo: pago de transporte",
                }
            ),

            "referencia": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Opcional",
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
