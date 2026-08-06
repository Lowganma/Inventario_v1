from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from usuarios.models import Negocio
from .models import Cliente


class ClienteSecurityTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user("owner", password="test-password-123")
        self.other = User.objects.create_user("other", password="test-password-123")
        self.business = Negocio.objects.create(propietario=self.owner, nombre="Uno")
        other_business = Negocio.objects.create(propietario=self.other, nombre="Dos")
        Cliente.objects.create(
            nombre="Privado", apellido="Uno", telefono="1", negocio=self.business
        )
        self.other_record = Cliente.objects.create(
            nombre="Ajeno", apellido="Dos", telefono="2", negocio=other_business
        )
        self.client.force_login(self.owner)

    def test_list_only_contains_current_business_clients(self):
        response = self.client.get(reverse("clientes:lista"))
        self.assertContains(response, "Privado")
        self.assertNotContains(response, "Ajeno")

    def test_cannot_edit_or_delete_another_business_client(self):
        for route in ("clientes:editar", "clientes:eliminar"):
            response = self.client.get(reverse(route, args=[self.other_record.id]))
            self.assertEqual(response.status_code, 404)
