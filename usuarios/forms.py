from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db import transaction

from .models import Negocio


class RegistroForm(UserCreationForm):
    """
    Crea simultáneamente un usuario y su negocio.

    Hereda de UserCreationForm para aprovechar:
    - validación de contraseñas;
    - confirmación de contraseña;
    - almacenamiento seguro de la contraseña.
    """

    email = forms.EmailField(
        label="Correo electrónico",
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "correo@ejemplo.com",
                "autocomplete": "email",
            }
        ),
    )

    nombre_negocio = forms.CharField(
        label="Nombre del negocio",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Ejemplo: Papelería Central",
            }
        ),
    )

    telefono_negocio = forms.CharField(
        label="Teléfono del negocio",
        max_length=20,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Ejemplo: 0412 1234567",
                "autocomplete": "tel",
            }
        ),
    )

    class Meta:
        model = User

        fields = [
            "username",
            "email",
            "nombre_negocio",
            "telefono_negocio",
            "password1",
            "password2",
        ]

        labels = {
            "username": "Nombre de usuario",
        }

        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Elige un nombre de usuario",
                    "autocomplete": "username",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        """
        Agrega las clases visuales de Bootstrap a los campos de
        contraseña heredados de UserCreationForm.
        """
        super().__init__(*args, **kwargs)

        self.fields["password1"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Crea una contraseña",
                "autocomplete": "new-password",
            }
        )

        self.fields["password2"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Repite la contraseña",
                "autocomplete": "new-password",
            }
        )

    def clean_email(self):
        """
        Evita registrar dos usuarios con el mismo correo.
        """
        email = self.cleaned_data["email"].lower().strip()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Ya existe una cuenta registrada con este correo."
            )

        return email

    @transaction.atomic
    def save(self, commit=True):
        """
        Guarda el usuario y el negocio dentro de una transacción.

        Si alguna de las dos operaciones falla, no se guarda
        información incompleta.
        """
        usuario = super().save(commit=False)

        usuario.email = self.cleaned_data["email"]

        if commit:
            usuario.save()

            Negocio.objects.create(
                propietario=usuario,
                nombre=self.cleaned_data["nombre_negocio"],
                telefono=self.cleaned_data["telefono_negocio"],
            )

        return usuario