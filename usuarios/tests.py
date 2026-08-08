from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import ModuloNegocio, Negocio, PerfilUsuario
from .services import actualizar_modulos


class AuthenticationRoutesTests(TestCase):
    def test_registration_is_public_and_does_not_redirect(self):
        response = self.client.get(reverse("usuarios:registro"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain, [])

    def test_protected_route_redirects_to_real_login_page(self):
        response = self.client.get(reverse("clientes:lista"))
        self.assertRedirects(
            response,
            f'{reverse("login")}?next={reverse("clientes:lista")}',
        )

    def test_legacy_user_without_business_has_no_redirect_loop(self):
        user = User.objects.create_user("legacy", password="safe-password-123")
        self.client.force_login(user)
        response = self.client.get(reverse("inicio"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertLess(len(response.redirect_chain), 2)
        self.assertTrue(hasattr(user, "negocio"))


class RolesYModulosTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user("admin", password="clave-segura")
        self.negocio = Negocio.objects.create(propietario=self.admin, nombre="Principal")
        self.empleado = User.objects.create_user("empleado", password="clave-segura")
        PerfilUsuario.objects.create(usuario=self.empleado, negocio=self.negocio, rol="empleado")

    def test_admin_gestiona_modulos_y_empleado_no(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("configuracion_modulos")).status_code, 200)
        self.client.force_login(self.empleado)
        self.assertEqual(self.client.get(reverse("configuracion_modulos")).status_code, 403)
        self.assertEqual(self.client.get(reverse("usuarios:lista")).status_code, 403)

    def test_modulo_inactivo_bloquea_url_oculta_navbar_y_se_puede_reactivar(self):
        self.client.force_login(self.admin)
        modulo = ModuloNegocio.objects.get(negocio=self.negocio, modulo="ventas")
        modulo.activo = False
        modulo.save()
        respuesta = self.client.get(reverse("ventas:lista"))
        self.assertEqual(respuesta.status_code, 403)
        inicio = self.client.get(reverse("inicio"))
        self.assertNotContains(inicio, reverse("ventas:lista"))
        modulo.activo = True
        modulo.save()
        self.assertEqual(self.client.get(reverse("ventas:lista")).status_code, 200)

    def test_dependencias_de_ventas_y_compras(self):
        with self.assertRaises(ValidationError):
            actualizar_modulos(negocio=self.negocio, seleccionados=["ventas"])
        with self.assertRaises(ValidationError):
            actualizar_modulos(negocio=self.negocio, seleccionados=["compras"])

    def test_configuracion_aislada_por_negocio(self):
        otro_admin = User.objects.create_user("admin2")
        otro = Negocio.objects.create(propietario=otro_admin, nombre="Otro")
        actualizar_modulos(negocio=self.negocio, seleccionados=["clientes"])
        self.assertTrue(ModuloNegocio.objects.get(negocio=otro, modulo="ventas").activo)
