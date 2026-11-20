import re
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class RecuperacionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("ana", email="ana@example.org", password="Inicial-79851")

    def solicitar(self, correo):
        return self.client.post(reverse("password_reset"), {"email": correo})

    def enlace(self):
        self.solicitar(self.user.email)
        return re.search(r"http://testserver(/recuperar/clave/\S+)", mail.outbox[0].body)[1]

    def test_correo_clave_y_enlace_de_un_solo_uso(self):
        enlace = self.enlace()
        respuesta = self.client.get(enlace, follow=True)
        self.assertContains(respuesta, "Elige una nueva contraseña")
        destino = respuesta.redirect_chain[-1][0]
        respuesta = self.client.post(destino, {"new_password1": "abc", "new_password2": "x"})
        self.assertFormError(respuesta.context["form"], "new_password2", "The two password fields didn’t match.")
        clave = "Nueva-Clave-8961"
        self.assertRedirects(self.client.post(destino, {"new_password1": clave, "new_password2": clave}),
                             reverse("password_reset_complete"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(clave))
        self.assertContains(self.client.get(enlace, follow=True), "Enlace no disponible")

    def test_solicitudes_misma_respuesta_publica(self):
        self.assertRedirects(self.solicitar("desconocida@example.org"), reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 0)
        self.assertRedirects(self.solicitar(self.user.email), reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)

    def test_enlace_caducado(self):
        enlace = self.enlace()
        with override_settings(PASSWORD_RESET_TIMEOUT=-1):
            self.assertContains(self.client.get(enlace, follow=True), "Enlace no disponible")

    def test_fallo_smtp_tiene_misma_respuesta(self):
        with patch("django.core.mail.message.EmailMultiAlternatives.send", side_effect=OSError), self.assertLogs("django.contrib.auth", level="ERROR"):
            self.assertRedirects(self.solicitar(self.user.email), reverse("password_reset_done"))
