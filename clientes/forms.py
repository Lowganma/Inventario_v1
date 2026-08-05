from django import forms

from .models import Cliente


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            "nombre",
            "apellido",
            "telefono",
            "estado",
        ]

        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ejemplo: Juan",
                    "autocomplete": "given-name",
                }
            ),
            "apellido": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ejemplo: Pérez",
                    "autocomplete": "family-name",
                }
            ),
            "telefono": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ejemplo: 0412 1234567",
                    "autocomplete": "tel",
                }
            ),
            "estado": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
        }

        labels = {
            "nombre": "Nombre",
            "apellido": "Apellido",
            "telefono": "Teléfono",
            "estado": "Estado del cliente",
        }

        help_texts = {
            "telefono": "Ingresa un número que permita contactar al cliente.",
            "estado": "Un cliente suspendido seguirá conservando sus cuentas.",
        }