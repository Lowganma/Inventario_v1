from django import forms

from .models import CuentaPorCobrar, Abono


class CuentaPorCobrarForm(forms.ModelForm):
    class Meta:
        model = CuentaPorCobrar

        fields = [
            "cliente",
            "concepto",
            "monto_total",
            "fecha_vencimiento",
            "notas",
        ]

        widgets = {
            "cliente": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "concepto": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ejemplo: compra fiada, servicio o préstamo",
                }
            ),
            "monto_total": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "0.00",
                    "min": "0.01",
                    "step": "0.01",
                }
            ),
            "fecha_vencimiento": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "estado": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "notas": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Información adicional sobre esta cuenta",
                }
            ),
        }

        labels = {
            "cliente": "Cliente",
            "concepto": "Concepto de la deuda",
            "monto_total": "Monto total",
            "fecha_vencimiento": "Fecha de vencimiento",
            "estado": "Estado",
            "notas": "Notas",
        }

        help_texts = {
            "cliente": "Selecciona la persona responsable de esta cuenta.",
            "fecha_vencimiento": "Este campo puede dejarse vacío.",
            "estado": "Las cuentas nuevas normalmente comienzan como pendientes.",
        }

class AbonoForm(forms.ModelForm):
    class Meta:
        model = Abono

        fields = [
            "monto_pagado",
            "fecha_pago",
            "metodo",
            "referencia",
            "notas",
        ]

        widgets = {
            "monto_pagado": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "0.00",
                    "min": "0.01",
                    "step": "0.01",
                }
            ),
            "fecha_pago": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "metodo": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "referencia": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Número de referencia o comprobante",
                }
            ),
            "notas": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Información adicional sobre el abono",
                }
            ),
        }

        labels = {
            "monto_pagado": "Monto del abono",
            "fecha_pago": "Fecha del pago",
            "metodo": "Método de pago",
            "referencia": "Referencia",
            "notas": "Notas",
        }

        help_texts = {
            "monto_pagado": "No puede ser mayor al saldo pendiente.",
            "referencia": "Puede dejarse vacío para pagos en efectivo.",
        }

    def __init__(self, *args, cuenta=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cuenta = cuenta

    def clean_monto_pagado(self):
        monto = self.cleaned_data["monto_pagado"]

        if monto <= 0:
            raise forms.ValidationError(
                "El monto debe ser mayor que cero."
            )

        if self.cuenta and monto > self.cuenta.saldo_pendiente:
            raise forms.ValidationError(
                "El abono no puede ser mayor al saldo pendiente."
            )

        return monto