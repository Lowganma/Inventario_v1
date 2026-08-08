from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Negocio
from .services import crear_modulos_por_defecto


@receiver(post_save, sender=Negocio)
def activar_modulos_nuevo_negocio(sender, instance, created, **kwargs):
    if created:
        crear_modulos_por_defecto(instance)
