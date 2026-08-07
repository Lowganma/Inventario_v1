from django import forms

from .models import Categoria, Producto


class CategoriaForm(forms.ModelForm):
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


class ProductoForm(forms.ModelForm):
    def __init__(self, *args, negocio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.negocio = negocio
        # La lista nunca expone categorías de otra empresa.
        self.fields["categoria"].queryset = (
            Categoria.objects.filter(negocio=negocio) if negocio else Categoria.objects.none()
        )

    class Meta:
        model = Producto
        fields = [
            "categoria",
            "codigo",
            "nombre",
            "descripcion",
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
        labels = {"precio_venta": "Precio de venta", "stock_minimo": "Stock mínimo"}
        help_texts = {
            "codigo": "Opcional. Si lo indicas, no podrá repetirse en tu negocio.",
            "stock_minimo": "Se avisará cuando el stock sea igual o menor a este valor.",
        }

    def clean_categoria(self):
        categoria = self.cleaned_data["categoria"]
        if not self.negocio or categoria.negocio_id != self.negocio.id:
            raise forms.ValidationError("Selecciona una categoría de tu negocio.")
        return categoria
