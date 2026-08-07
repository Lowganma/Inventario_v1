from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("productos", "0004_asociar_datos_existentes")]
    operations = [
        migrations.AlterField(model_name="categoria", name="fecha_creacion", field=models.DateTimeField(auto_now_add=True)),
        migrations.AlterField(model_name="categoria", name="negocio", field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="categorias_producto", to="usuarios.negocio")),
        migrations.AlterField(model_name="producto", name="negocio", field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="productos", to="usuarios.negocio")),
        migrations.AlterField(model_name="producto", name="costo", field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12, validators=[MinValueValidator(Decimal("0.00"))])),
        migrations.AlterField(model_name="producto", name="precio_venta", field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12, validators=[MinValueValidator(Decimal("0.00"))])),
        migrations.AddConstraint(model_name="categoria", constraint=models.UniqueConstraint(fields=("negocio", "nombre"), name="categoria_nombre_unico_por_negocio")),
        migrations.AddConstraint(model_name="producto", constraint=models.UniqueConstraint(condition=~models.Q(codigo=""), fields=("negocio", "codigo"), name="producto_codigo_unico_por_negocio")),
        migrations.AddConstraint(model_name="producto", constraint=models.CheckConstraint(check=models.Q(stock__gte=0), name="producto_stock_no_negativo")),
        migrations.AddConstraint(model_name="producto", constraint=models.CheckConstraint(check=models.Q(stock_minimo__gte=0), name="producto_stock_minimo_no_negativo")),
        migrations.AddConstraint(model_name="producto", constraint=models.CheckConstraint(check=models.Q(costo__gte=0), name="producto_costo_no_negativo")),
        migrations.AddConstraint(model_name="producto", constraint=models.CheckConstraint(check=models.Q(precio_venta__gte=0), name="producto_precio_no_negativo")),
    ]
