from datetime import timedelta

from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from bookings.models import Booking, Room

LOGIN_URL_NAME = "auth-login"
LOGOUT_URL_NAME = "auth-logout"
ME_URL_NAME = "auth-me"
CSRF_URL_NAME = "auth-csrf"
ADMIN_USER_LIST_URL_NAME = "admin-user-list"
ADMIN_USER_DETAIL_URL_NAME = "admin-user-detail"

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


class AdminUserManagementTests(APITestCase):
    def setUp(self):
        self.password = "correct-horse-battery"
        self.admin = User.objects.create_user(
            username="admin1", password=self.password, is_staff=True
        )
        self.other_admin = User.objects.create_user(
            username="admin2", password=self.password, is_staff=True
        )
        self.employee = User.objects.create_user(username="alice", password=self.password)

    def test_anonymous_user_cannot_list_users(self):
        response = self.client.get(reverse(ADMIN_USER_LIST_URL_NAME))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_employee_cannot_list_users(self):
        self.client.login(username="alice", password=self.password)

        response = self.client.get(reverse(ADMIN_USER_LIST_URL_NAME))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_employee_cannot_create_user(self):
        self.client.login(username="alice", password=self.password)

        response = self.client.post(
            reverse(ADMIN_USER_LIST_URL_NAME),
            {"username": "bob", "password": "a-strong-password"},
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_employee_cannot_patch_user(self):
        self.client.login(username="alice", password=self.password)

        response = self.client.patch(
            reverse(ADMIN_USER_DETAIL_URL_NAME, args=[self.other_admin.id]),
            {"is_active": False},
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_user(self):
        self.client.login(username="admin1", password=self.password)

        response = self.client.post(
            reverse(ADMIN_USER_LIST_URL_NAME),
            {"username": "bob", "password": "a-strong-password", "is_staff": False},
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        body = response.json()
        self.assertEqual(body["username"], "bob")
        self.assertEqual(body["is_staff"], False)
        self.assertEqual(body["is_active"], True)
        self.assertEqual(body["upcoming_booking_count"], 0)
        self.assertNotIn("password", body)
        self.assertTrue(User.objects.get(username="bob").check_password("a-strong-password"))

    def test_weak_password_rejected_on_create(self):
        self.client.login(username="admin1", password=self.password)

        response = self.client.post(
            reverse(ADMIN_USER_LIST_URL_NAME),
            {"username": "bob", "password": "short"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.json())
        self.assertFalse(User.objects.filter(username="bob").exists())

    def test_password_required_on_create(self):
        self.client.login(username="admin1", password=self.password)

        response = self.client.post(
            reverse(ADMIN_USER_LIST_URL_NAME),
            {"username": "bob"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.json())

    def test_list_includes_upcoming_booking_count(self):
        room = Room.objects.create(name="Falcon", capacity=8, location="3F")
        now = timezone.now()
        Booking.objects.create(
            room=room,
            user=self.employee,
            title="Upcoming",
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
        )
        self.client.login(username="admin1", password=self.password)

        response = self.client.get(reverse(ADMIN_USER_LIST_URL_NAME))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body_by_username = {user["username"]: user for user in response.json()}
        self.assertEqual(body_by_username["alice"]["upcoming_booking_count"], 1)
        self.assertEqual(body_by_username["admin1"]["upcoming_booking_count"], 0)

    def test_username_cannot_be_changed_via_patch(self):
        self.client.login(username="admin1", password=self.password)

        response = self.client.patch(
            reverse(ADMIN_USER_DETAIL_URL_NAME, args=[self.employee.id]),
            {"username": "renamed"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.username, "alice")

    def test_password_never_appears_in_patch_response(self):
        self.client.login(username="admin1", password=self.password)

        response = self.client.patch(
            reverse(ADMIN_USER_DETAIL_URL_NAME, args=[self.employee.id]),
            {"password": "a-different-strong-password"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("password", response.json())
        self.employee.refresh_from_db()
        self.assertTrue(self.employee.check_password("a-different-strong-password"))

    def test_br9_admin_cannot_deactivate_own_account(self):
        self.client.login(username="admin1", password=self.password)

        response = self.client.patch(
            reverse(ADMIN_USER_DETAIL_URL_NAME, args=[self.admin.id]),
            {"is_active": False},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("BR-9", response.json()["detail"])
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_br9_admin_cannot_demote_own_account(self):
        self.client.login(username="admin1", password=self.password)

        response = self.client.patch(
            reverse(ADMIN_USER_DETAIL_URL_NAME, args=[self.admin.id]),
            {"is_staff": False},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("BR-9", response.json()["detail"])
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_staff)

    def test_admin_can_deactivate_other_admin(self):
        self.client.login(username="admin1", password=self.password)

        response = self.client.patch(
            reverse(ADMIN_USER_DETAIL_URL_NAME, args=[self.other_admin.id]),
            {"is_active": False},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.other_admin.refresh_from_db()
        self.assertFalse(self.other_admin.is_active)

    def test_deactivated_user_cannot_log_in(self):
        self.client.login(username="admin1", password=self.password)
        self.client.patch(
            reverse(ADMIN_USER_DETAIL_URL_NAME, args=[self.employee.id]),
            {"is_active": False},
        )
        self.client.logout()

        response = self.client.post(
            reverse(LOGIN_URL_NAME),
            {"username": "alice", "password": self.password},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"non_field_errors": [SAME_CREDENTIALS_ERROR]})

    def test_deactivating_user_cancels_future_bookings_but_keeps_past_ones(self):
        room = Room.objects.create(name="Falcon", capacity=8, location="3F")
        now = timezone.now()
        future_booking = Booking.objects.create(
            room=room,
            user=self.employee,
            title="Future",
            start_time=now + timedelta(hours=2),
            end_time=now + timedelta(hours=3),
        )
        past_booking = Booking.objects.create(
            room=room,
            user=self.employee,
            title="Past",
            start_time=now - timedelta(hours=3),
            end_time=now - timedelta(hours=2),
        )
        self.client.login(username="admin1", password=self.password)

        response = self.client.patch(
            reverse(ADMIN_USER_DETAIL_URL_NAME, args=[self.employee.id]),
            {"is_active": False},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["cancelled_bookings_count"], 1)
        self.assertFalse(Booking.objects.filter(pk=future_booking.pk).exists())
        self.assertTrue(Booking.objects.filter(pk=past_booking.pk).exists())

    def test_cancelled_bookings_count_absent_when_not_deactivating(self):
        self.client.login(username="admin1", password=self.password)

        response = self.client.patch(
            reverse(ADMIN_USER_DETAIL_URL_NAME, args=[self.employee.id]),
            {"is_staff": True},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("cancelled_bookings_count", response.json())

    def test_delete_always_returns_405(self):
        response = self.client.delete(reverse(ADMIN_USER_DETAIL_URL_NAME, args=[self.employee.id]))
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        self.client.login(username="admin1", password=self.password)
        response = self.client.delete(reverse(ADMIN_USER_DETAIL_URL_NAME, args=[self.employee.id]))
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
