from django.core.management.base import BaseCommand

from cuentas.services.tasa_bcv import (
    ErrorConsultaBCV,
    actualizar_tasa_dolar_bcv,
)


class Command(BaseCommand):
    """
    Actualiza manualmente la tasa USD/VES utilizada
    como referencia por el sistema.
    """

    help = "Consulta y actualiza la tasa BCV del dólar."


    def handle(self, *args, **options):

        try:

            tasa, creada = actualizar_tasa_dolar_bcv()

        except ErrorConsultaBCV as error:

            self.stderr.write(
                self.style.ERROR(
                    f"No fue posible actualizar la tasa: {error}"
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
                f"Tasa BCV {accion}: "
                f"1 USD = {tasa.valor} Bs. "
                f"({tasa.fecha_vigencia})"
            )
        )