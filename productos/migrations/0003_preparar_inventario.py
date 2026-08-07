# Migración en dos fases: primero admite negocio nulo para conservar datos previos.
from decimal import Decimal

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("productos", "0002_producto_creado_en"), ("usuarios", "0001_initial")]

    operations = [
        migrations.AddField(model_name="categoria", name="activa", field=models.BooleanField(default=True)),
        migrations.AddField(model_name="categoria", name="color", field=models.CharField(default="#0d6efd", max_length=7)),
        migrations.AddField(model_name="categoria", name="descripcion", field=models.TextField(blank=True)),
        migrations.AddField(model_name="categoria", name="fecha_creacion", field=models.DateTimeField(auto_now_add=True, null=True)),
        migrations.AddField(model_name="categoria", name="negocio", field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name="categorias_producto", to="usuarios.negocio")),
        migrations.RenameField(model_name="producto", old_name="creado_en", new_name="fecha_creacion"),
        migrations.AlterField(model_name="producto", name="fecha_creacion", field=models.DateTimeField(auto_now_add=True)),
        migrations.AlterField(model_name="producto", name="categoria", field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="productos", to="productos.categoria")),
        migrations.AlterField(model_name="producto", name="stock", field=models.PositiveIntegerField(default=0)),
        migrations.AddField(model_name="producto", name="activo", field=models.BooleanField(default=True)),
        migrations.AddField(model_name="producto", name="codigo", field=models.CharField(blank=True, max_length=100)),
        migrations.AddField(model_name="producto", name="costo", field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12)),
        migrations.AddField(model_name="producto", name="descripcion", field=models.TextField(blank=True)),
        migrations.AddField(model_name="producto", name="fecha_actualizacion", field=models.DateTimeField(auto_now=True)),
        migrations.AddField(model_name="producto", name="negocio", field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name="productos", to="usuarios.negocio")),
        migrations.AddField(model_name="producto", name="precio_venta", field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12)),
        migrations.AddField(model_name="producto", name="stock_minimo", field=models.PositiveIntegerField(default=0)),
        migrations.RemoveField(model_name="producto", name="puntaje"),
        migrations.AlterModelOptions(name="categoria", options={"ordering": ["nombre"]}),
        migrations.AlterModelOptions(name="producto", options={"ordering": ["nombre"]}),
    ]
