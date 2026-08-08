from django.db import migrations

MODULOS = ("clientes", "cuentas", "inventario", "compras", "ventas", "caja")


def crear_configuraciones(apps, schema_editor):
    Negocio = apps.get_model("usuarios", "Negocio")
    ModuloNegocio = apps.get_model("usuarios", "ModuloNegocio")
    for negocio in Negocio.objects.all().iterator():
        for modulo in MODULOS:
            ModuloNegocio.objects.get_or_create(negocio=negocio, modulo=modulo, defaults={"activo": True})


class Migration(migrations.Migration):
    dependencies = [("usuarios", "0002_perfilusuario_modulonegocio_and_more")]
    operations = [migrations.RunPython(crear_configuraciones, migrations.RunPython.noop)]
