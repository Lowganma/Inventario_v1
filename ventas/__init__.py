def __init__(
    self,
    *args,
    negocio=None,
    **kwargs,
):
    super().__init__(
        *args,
        **kwargs,
    )

    if negocio:

        self.fields["producto"].queryset = (
            Producto.objects.filter(
                negocio=negocio,
                activo=True,
            )
            .select_related("categoria")
            .order_by("nombre")
        )

        self.fields["presentacion"].queryset = (
            PresentacionProducto.objects.filter(
                producto__negocio=negocio,
                activa=True,
            )
            .select_related("producto")
            .order_by(
                "producto__nombre",
                "cantidad_unidades",
            )
        )

    else:

        self.fields["producto"].queryset = (
            Producto.objects.none()
        )

        self.fields["presentacion"].queryset = (
            PresentacionProducto.objects.none()
        )