from datetime import timedelta

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from bookings.models import Booking, Room


def next_quarter_hour(moment):
    discard = timedelta(
        minutes=moment.minute % 15, seconds=moment.second, microseconds=moment.microsecond
    )
    aligned = moment - discard
    if discard:
        aligned += timedelta(minutes=15)
    return aligned


class RoomListTests(APITestCase):
    def setUp(self):
        self.password = "correct-horse-battery"
        self.employee = User.objects.create_user(username="alice", password=self.password)
        self.admin = User.objects.create_user(
            username="admin1", password=self.password, is_staff=True
        )
        self.active_room = Room.objects.create(name="Falcon", capacity=8, location="3F")
        self.inactive_room = Room.objects.create(
            name="Hawk", capacity=4, location="2F", is_active=False
        )

    def test_anonymous_user_cannot_list_rooms(self):
        response = self.client.get(reverse("room-list"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_employee_sees_only_active_rooms(self):
        self.client.login(username="alice", password=self.password)

        response = self.client.get(reverse("room-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = {room["name"] for room in response.json()}
        self.assertEqual(names, {"Falcon"})

    def test_admin_sees_all_rooms(self):
        self.client.login(username="admin1", password=self.password)

        response = self.client.get(reverse("room-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = {room["name"] for room in response.json()}
        self.assertEqual(names, {"Falcon", "Hawk"})


class RoomDetailTests(APITestCase):
    def setUp(self):
        self.password = "correct-horse-battery"
        self.employee = User.objects.create_user(username="alice", password=self.password)
        self.admin = User.objects.create_user(
            username="admin1", password=self.password, is_staff=True
        )
        self.active_room = Room.objects.create(name="Falcon", capacity=8, location="3F")
        self.inactive_room = Room.objects.create(
            name="Hawk", capacity=4, location="2F", is_active=False
        )

    def test_anonymous_user_cannot_retrieve_room(self):
        response = self.client.get(reverse("room-detail", args=[self.active_room.id]))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_employee_can_retrieve_active_room(self):
        self.client.login(username="alice", password=self.password)

        response = self.client.get(reverse("room-detail", args=[self.active_room.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["name"], "Falcon")

    def test_employee_gets_404_for_inactive_room(self):
        self.client.login(username="alice", password=self.password)

        response = self.client.get(reverse("room-detail", args=[self.inactive_room.id]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_can_retrieve_inactive_room(self):
        self.client.login(username="admin1", password=self.password)

        response = self.client.get(reverse("room-detail", args=[self.inactive_room.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["name"], "Hawk")

    def test_unknown_room_id_returns_404(self):
        self.client.login(username="alice", password=self.password)

        response = self.client.get(reverse("room-detail", args=[999999]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class RoomCreateTests(APITestCase):
    def setUp(self):
        self.password = "correct-horse-battery"
        self.employee = User.objects.create_user(username="alice", password=self.password)
        self.admin = User.objects.create_user(
            username="admin1", password=self.password, is_staff=True
        )

    def test_anonymous_user_cannot_create_room(self):
        response = self.client.post(
            reverse("room-list"), {"name": "Falcon", "capacity": 8, "location": "3F"}
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_employee_cannot_create_room(self):
        self.client.login(username="alice", password=self.password)

        response = self.client.post(
            reverse("room-list"), {"name": "Falcon", "capacity": 8, "location": "3F"}
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_room(self):
        self.client.login(username="admin1", password=self.password)

        response = self.client.post(
            reverse("room-list"), {"name": "Falcon", "capacity": 8, "location": "3F"}
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.json(),
            {
                "id": response.json()["id"],
                "name": "Falcon",
                "capacity": 8,
                "location": "3F",
                "is_active": True,
                "created_at": response.json()["created_at"],
            },
        )

    def test_duplicate_name_returns_400(self):
        Room.objects.create(name="Falcon", capacity=8, location="3F")
        self.client.login(username="admin1", password=self.password)

        response = self.client.post(
            reverse("room-list"), {"name": "Falcon", "capacity": 4, "location": "2F"}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.json())

    def test_capacity_below_minimum_returns_400(self):
        self.client.login(username="admin1", password=self.password)

        response = self.client.post(
            reverse("room-list"), {"name": "Falcon", "capacity": 0, "location": "3F"}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("capacity", response.json())

    def test_capacity_above_maximum_returns_400(self):
        self.client.login(username="admin1", password=self.password)

        response = self.client.post(
            reverse("room-list"), {"name": "Falcon", "capacity": 101, "location": "3F"}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("capacity", response.json())


class RoomUpdateTests(APITestCase):
    def setUp(self):
        self.password = "correct-horse-battery"
        self.employee = User.objects.create_user(username="alice", password=self.password)
        self.admin = User.objects.create_user(
            username="admin1", password=self.password, is_staff=True
        )
        self.room = Room.objects.create(name="Falcon", capacity=8, location="3F")

    def test_anonymous_user_cannot_patch_room(self):
        response = self.client.patch(
            reverse("room-detail", args=[self.room.id]), {"is_active": False}
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_employee_cannot_patch_room(self):
        self.client.login(username="alice", password=self.password)

        response = self.client.patch(
            reverse("room-detail", args=[self.room.id]), {"is_active": False}
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_patch_room(self):
        self.client.login(username="admin1", password=self.password)

        response = self.client.patch(
            reverse("room-detail", args=[self.room.id]), {"is_active": False}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.room.refresh_from_db()
        self.assertFalse(self.room.is_active)

    def test_patch_unknown_room_returns_404(self):
        self.client.login(username="admin1", password=self.password)

        response = self.client.patch(reverse("room-detail", args=[999999]), {"is_active": False})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class RoomDeleteAndPutTests(APITestCase):
    def setUp(self):
        self.password = "correct-horse-battery"
        self.admin = User.objects.create_user(
            username="admin1", password=self.password, is_staff=True
        )
        self.room = Room.objects.create(name="Falcon", capacity=8, location="3F")

    def test_delete_always_returns_405(self):
        response = self.client.delete(reverse("room-detail", args=[self.room.id]))
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        self.client.login(username="admin1", password=self.password)
        response = self.client.delete(reverse("room-detail", args=[self.room.id]))
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_put_always_returns_405(self):
        response = self.client.put(
            reverse("room-detail", args=[self.room.id]),
            {"name": "Falcon", "capacity": 8, "location": "3F"},
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        self.client.login(username="admin1", password=self.password)
        response = self.client.put(
            reverse("room-detail", args=[self.room.id]),
            {"name": "Falcon", "capacity": 8, "location": "3F"},
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class BookingCreateTests(APITestCase):
    def setUp(self):
        self.password = "correct-horse-battery"
        self.alice = User.objects.create_user(username="alice", password=self.password)
        self.room = Room.objects.create(name="Falcon", capacity=8, location="3F")
        self.start = next_quarter_hour(timezone.now() + timedelta(hours=2))

    def test_anonymous_user_cannot_create_booking(self):
        response = self.client.post(
            reverse("booking-list"),
            {
                "room": self.room.id,
                "title": "Sprint planning",
                "start_time": self.start.isoformat(),
                "end_time": (self.start + timedelta(hours=1)).isoformat(),
            },
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_employee_can_create_booking(self):
        self.client.login(username="alice", password=self.password)

        response = self.client.post(
            reverse("booking-list"),
            {
                "room": self.room.id,
                "title": "Sprint planning",
                "start_time": self.start.isoformat(),
                "end_time": (self.start + timedelta(hours=1)).isoformat(),
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        body = response.json()
        self.assertEqual(body["room"], {"id": self.room.id, "name": "Falcon"})
        self.assertEqual(body["title"], "Sprint planning")
        self.assertNotIn("user", body)

    def test_owner_is_set_from_request_user_not_request_body(self):
        other = User.objects.create_user(username="bob", password=self.password)
        self.client.login(username="alice", password=self.password)

        response = self.client.post(
            reverse("booking-list"),
            {
                "room": self.room.id,
                "user": other.id,
                "title": "Sprint planning",
                "start_time": self.start.isoformat(),
                "end_time": (self.start + timedelta(hours=1)).isoformat(),
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        booking = Booking.objects.get(pk=response.json()["id"])
        self.assertEqual(booking.user, self.alice)

    def test_br1_end_before_start(self):
        self.client.login(username="alice", password=self.password)

        response = self.client.post(
            reverse("booking-list"),
            {
                "room": self.room.id,
                "title": "Sprint planning",
                "start_time": self.start.isoformat(),
                "end_time": (self.start - timedelta(minutes=30)).isoformat(),
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("BR-1", str(response.json().get("end_time")))

    def test_br2_cannot_start_in_past(self):
        self.client.login(username="alice", password=self.password)
        past_start = next_quarter_hour(timezone.now() - timedelta(hours=1))

        response = self.client.post(
            reverse("booking-list"),
            {
                "room": self.room.id,
                "title": "Sprint planning",
                "start_time": past_start.isoformat(),
                "end_time": (past_start + timedelta(hours=1)).isoformat(),
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("BR-2", str(response.json().get("start_time")))

    def test_br3_max_four_hours(self):
        self.client.login(username="alice", password=self.password)

        response = self.client.post(
            reverse("booking-list"),
            {
                "room": self.room.id,
                "title": "Sprint planning",
                "start_time": self.start.isoformat(),
                "end_time": (self.start + timedelta(hours=4, minutes=15)).isoformat(),
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("BR-3", str(response.json().get("end_time")))

    def test_br4_start_not_on_quarter_hour(self):
        self.client.login(username="alice", password=self.password)
        misaligned_start = self.start + timedelta(minutes=5)

        response = self.client.post(
            reverse("booking-list"),
            {
                "room": self.room.id,
                "title": "Sprint planning",
                "start_time": misaligned_start.isoformat(),
                "end_time": (misaligned_start + timedelta(hours=1)).isoformat(),
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("BR-4", str(response.json().get("start_time")))

    def test_br4_end_not_on_quarter_hour(self):
        self.client.login(username="alice", password=self.password)

        response = self.client.post(
            reverse("booking-list"),
            {
                "room": self.room.id,
                "title": "Sprint planning",
                "start_time": self.start.isoformat(),
                "end_time": (self.start + timedelta(hours=1, minutes=5)).isoformat(),
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("BR-4", str(response.json().get("end_time")))

    def test_br5_inactive_room_rejected(self):
        inactive_room = Room.objects.create(name="Hawk", capacity=4, location="2F", is_active=False)
        self.client.login(username="alice", password=self.password)

        response = self.client.post(
            reverse("booking-list"),
            {
                "room": inactive_room.id,
                "title": "Sprint planning",
                "start_time": self.start.isoformat(),
                "end_time": (self.start + timedelta(hours=1)).isoformat(),
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("BR-5", str(response.json().get("room")))


class BookingListTests(APITestCase):
    def setUp(self):
        self.password = "correct-horse-battery"
        self.alice = User.objects.create_user(username="alice", password=self.password)
        self.bob = User.objects.create_user(username="bob", password=self.password)
        self.room = Room.objects.create(name="Falcon", capacity=8, location="3F")
        now = timezone.now()

        self.upcoming = Booking.objects.create(
            room=self.room,
            user=self.alice,
            title="Upcoming",
            start_time=now + timedelta(hours=2),
            end_time=now + timedelta(hours=3),
        )
        self.later_upcoming = Booking.objects.create(
            room=self.room,
            user=self.alice,
            title="Later upcoming",
            start_time=now + timedelta(hours=5),
            end_time=now + timedelta(hours=6),
        )
        self.past = Booking.objects.create(
            room=self.room,
            user=self.alice,
            title="Past",
            start_time=now - timedelta(hours=3),
            end_time=now - timedelta(hours=2),
        )
        self.others_booking = Booking.objects.create(
            room=self.room,
            user=self.bob,
            title="Bob's booking",
            start_time=now + timedelta(hours=2),
            end_time=now + timedelta(hours=3),
        )

    def test_anonymous_user_cannot_list_bookings(self):
        response = self.client.get(reverse("booking-list"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_defaults_to_upcoming_own_bookings_ordered_by_start_time(self):
        self.client.login(username="alice", password=self.password)

        response = self.client.get(reverse("booking-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [booking["title"] for booking in response.json()]
        self.assertEqual(titles, ["Upcoming", "Later upcoming"])

    def test_list_past_true_returns_only_past_own_bookings(self):
        self.client.login(username="alice", password=self.password)

        response = self.client.get(reverse("booking-list"), {"past": "true"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [booking["title"] for booking in response.json()]
        self.assertEqual(titles, ["Past"])

    def test_list_never_includes_other_users_bookings(self):
        self.client.login(username="alice", password=self.password)

        response = self.client.get(reverse("booking-list"))

        titles = [booking["title"] for booking in response.json()]
        self.assertNotIn("Bob's booking", titles)


class BookingDetailTests(APITestCase):
    def setUp(self):
        self.password = "correct-horse-battery"
        self.alice = User.objects.create_user(username="alice", password=self.password)
        self.bob = User.objects.create_user(username="bob", password=self.password)
        self.room = Room.objects.create(name="Falcon", capacity=8, location="3F")
        now = timezone.now()

        self.alices_booking = Booking.objects.create(
            room=self.room,
            user=self.alice,
            title="Sprint planning",
            start_time=now + timedelta(hours=2),
            end_time=now + timedelta(hours=3),
        )
        self.started_booking = Booking.objects.create(
            room=self.room,
            user=self.alice,
            title="Already started",
            start_time=now - timedelta(minutes=30),
            end_time=now + timedelta(minutes=30),
        )

    def test_anonymous_user_cannot_retrieve_booking(self):
        response = self.client.get(reverse("booking-detail", args=[self.alices_booking.id]))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_owner_can_retrieve_own_booking(self):
        self.client.login(username="alice", password=self.password)

        response = self.client.get(reverse("booking-detail", args=[self.alices_booking.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["title"], "Sprint planning")

    def test_br7_other_employee_cannot_view_booking(self):
        self.client.login(username="bob", password=self.password)

        response = self.client.get(reverse("booking-detail", args=[self.alices_booking.id]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_br7_other_employee_cannot_patch_booking(self):
        self.client.login(username="bob", password=self.password)

        response = self.client.patch(
            reverse("booking-detail", args=[self.alices_booking.id]), {"title": "Hijacked"}
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_br7_other_employee_cannot_delete_booking(self):
        self.client.login(username="bob", password=self.password)

        response = self.client.delete(reverse("booking-detail", args=[self.alices_booking.id]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_can_patch_future_booking(self):
        self.client.login(username="alice", password=self.password)

        response = self.client.patch(
            reverse("booking-detail", args=[self.alices_booking.id]),
            {"title": "Sprint planning (updated)"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["title"], "Sprint planning (updated)")

    def test_owner_can_delete_future_booking(self):
        self.client.login(username="alice", password=self.password)

        response = self.client.delete(reverse("booking-detail", args=[self.alices_booking.id]))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Booking.objects.filter(pk=self.alices_booking.id).exists())

    def test_br7_cannot_patch_started_booking(self):
        self.client.login(username="alice", password=self.password)

        response = self.client.patch(
            reverse("booking-detail", args=[self.started_booking.id]), {"title": "Too late"}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("BR-7", str(response.json()))

    def test_br7_cannot_delete_started_booking(self):
        self.client.login(username="alice", password=self.password)

        response = self.client.delete(reverse("booking-detail", args=[self.started_booking.id]))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("BR-7", str(response.json()))

    def test_unknown_booking_id_returns_404(self):
        self.client.login(username="alice", password=self.password)

        response = self.client.get(reverse("booking-detail", args=[999999]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
