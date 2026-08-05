from django.contrib import admin

from .models import Cliente, Pago

# Register your models here.

admin.site.register(Cliente)
admin.site.register(Pago)