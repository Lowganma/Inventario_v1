from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


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
