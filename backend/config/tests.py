from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class HealthEndpointTests(APITestCase):
    def test_health_check_returns_ok_without_authentication(self):
        response = self.client.get(reverse("health"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"status": "ok"})


class ApiDocsPermissionTests(APITestCase):
    def setUp(self):
        self.password = "correct-horse-battery"
        self.employee = User.objects.create_user(username="alice", password=self.password)
        self.admin = User.objects.create_user(
            username="admin1", password=self.password, is_staff=True
        )

    def test_anonymous_user_cannot_access_schema_or_docs(self):
        schema_response = self.client.get(reverse("schema"))
        docs_response = self.client.get(reverse("docs"))

        # Not logged in at all -> 401, per docs/API.md's error table.
        self.assertEqual(schema_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(docs_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_employee_cannot_access_schema_or_docs(self):
        self.client.login(username="alice", password=self.password)

        schema_response = self.client.get(reverse("schema"))
        docs_response = self.client.get(reverse("docs"))

        self.assertEqual(schema_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(docs_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_access_schema_and_docs(self):
        self.client.login(username="admin1", password=self.password)

        schema_response = self.client.get(reverse("schema"))
        docs_response = self.client.get(reverse("docs"))

        self.assertEqual(schema_response.status_code, status.HTTP_200_OK)
        self.assertEqual(docs_response.status_code, status.HTTP_200_OK)
