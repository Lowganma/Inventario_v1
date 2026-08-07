from django.db import migrations


def asociar_datos(apps, schema_editor):
    Categoria = apps.get_model("productos", "Categoria")
    Producto = apps.get_model("productos", "Producto")
    Negocio = apps.get_model("usuarios", "Negocio")
    if not (Categoria.objects.filter(negocio__isnull=True).exists() or Producto.objects.filter(negocio__isnull=True).exists()):
        return

    negocios = Negocio.objects.all()
    if negocios.count() != 1:
        raise RuntimeError(
            "Hay datos antiguos de productos sin negocio y no es posible inferir su dueño. "
            "Migra primero hasta productos 0003, asigna negocio_id a cada categoría y "
            "producto de forma controlada, y luego ejecuta migrate nuevamente."
        )

    # Solo una empresa permite una asociación inequívoca sin inventar identificadores.
    negocio = negocios.get()
    Categoria.objects.filter(negocio__isnull=True).update(negocio=negocio)
    Producto.objects.filter(negocio__isnull=True).update(negocio=negocio)


class Migration(migrations.Migration):
    dependencies = [("productos", "0003_preparar_inventario")]
    operations = [migrations.RunPython(asociar_datos, migrations.RunPython.noop)]
