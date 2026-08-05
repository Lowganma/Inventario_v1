from django.core.management.base import BaseCommand

from cuentas.services.tasa_bcv import (
    ErrorConsultaBCV,
    actualizar_tasa_dolar_bcv,
)


class Command(BaseCommand):
    help = (
        "Consulta exclusivamente la tasa USD oficial del BCV "
        "y la guarda en la base de datos."
    )

    def handle(self, *args, **options):
        try:
            tasa, creada = actualizar_tasa_dolar_bcv()

        except ErrorConsultaBCV as error:
            self.stderr.write(
                self.style.ERROR(
                    f"No se actualizó la tasa: {error}"
                )
            )
            return

        accion = (
            "creada"
            if creada
            else "actualizada"
        )

        self.stdout.write(
            self.style.SUCCESS(
                (
                    f"Tasa USD {accion}: "
                    f"Bs. {tasa.valor} | "
                    f"Vigencia: {tasa.fecha_vigencia}"
                )
            )
        )