from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

LOGIN_URL_NAME = "auth-login"
LOGOUT_URL_NAME = "auth-logout"
ME_URL_NAME = "auth-me"
CSRF_URL_NAME = "auth-csrf"

SAME_CREDENTIALS_ERROR = "Unable to log in with provided credentials."


class AuthenticationTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.password = "correct-horse-battery"
        self.user = User.objects.create_user(username="alice", password=self.password)

    def test_login_success_returns_user(self):
        response = self.client.post(
            reverse(LOGIN_URL_NAME),
            {"username": "alice", "password": self.password},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(), {"id": self.user.id, "username": "alice", "is_staff": False}
        )

    def test_login_wrong_password_returns_generic_error(self):
        response = self.client.post(
            reverse(LOGIN_URL_NAME),
            {"username": "alice", "password": "wrong-password"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"non_field_errors": [SAME_CREDENTIALS_ERROR]})

    def test_login_unknown_user_returns_same_generic_error(self):
        response = self.client.post(
            reverse(LOGIN_URL_NAME),
            {"username": "nobody", "password": "whatever123"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"non_field_errors": [SAME_CREDENTIALS_ERROR]})

    def test_login_inactive_user_cannot_log_in(self):
        self.user.is_active = False
        self.user.save()

        response = self.client.post(
            reverse(LOGIN_URL_NAME),
            {"username": "alice", "password": self.password},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"non_field_errors": [SAME_CREDENTIALS_ERROR]})

    def test_me_requires_authentication(self):
        response = self.client.get(reverse(ME_URL_NAME))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_current_user_when_logged_in(self):
        self.client.login(username="alice", password=self.password)

        response = self.client.get(reverse(ME_URL_NAME))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(), {"id": self.user.id, "username": "alice", "is_staff": False}
        )

    def test_logout_ends_the_session(self):
        self.client.login(username="alice", password=self.password)

        logout_response = self.client.post(reverse(LOGOUT_URL_NAME))
        self.assertEqual(logout_response.status_code, status.HTTP_204_NO_CONTENT)

        me_response = self.client.get(reverse(ME_URL_NAME))
        self.assertEqual(me_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_without_csrf_token_is_rejected(self):
        client = APIClient(enforce_csrf_checks=True)
        client.get(reverse(CSRF_URL_NAME))

        response = client.post(
            reverse(LOGIN_URL_NAME),
            {"username": "alice", "password": self.password},
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_sixth_login_attempt_in_a_minute_is_throttled(self):
        for _ in range(5):
            response = self.client.post(
                reverse(LOGIN_URL_NAME),
                {"username": "alice", "password": "wrong-password"},
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(
            reverse(LOGIN_URL_NAME),
            {"username": "alice", "password": "wrong-password"},
        )

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
