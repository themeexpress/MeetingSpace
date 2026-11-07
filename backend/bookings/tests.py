from datetime import UTC, datetime, timedelta

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
            start_time=now + timedelta(hours=8),
            end_time=now + timedelta(hours=9),
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


class RoomScheduleTests(APITestCase):
    def setUp(self):
        self.password = "correct-horse-battery"
        self.alice = User.objects.create_user(username="alice", password=self.password)
        self.bob = User.objects.create_user(username="bob", password=self.password)
        self.room = Room.objects.create(name="Falcon", capacity=8, location="3F")
        self.inactive_room = Room.objects.create(
            name="Hawk", capacity=4, location="2F", is_active=False
        )
        # 10:00-11:00 JST on 2026-11-09 -> 01:00-02:00 UTC same day.
        self.same_day_booking = Booking.objects.create(
            room=self.room,
            user=self.alice,
            title="Sprint planning",
            start_time=datetime(2026, 11, 9, 1, 0, tzinfo=UTC),
            end_time=datetime(2026, 11, 9, 2, 0, tzinfo=UTC),
        )
        # 23:30 JST on 2026-11-09 to 00:30 JST on 2026-11-10 -> spans midnight JST.
        self.spans_midnight_booking = Booking.objects.create(
            room=self.room,
            user=self.bob,
            title="Late sync",
            start_time=datetime(2026, 11, 9, 14, 30, tzinfo=UTC),
            end_time=datetime(2026, 11, 9, 15, 30, tzinfo=UTC),
        )

    def test_anonymous_user_cannot_view_schedule(self):
        response = self.client.get(
            reverse("room-schedule", args=[self.room.id]), {"date": "2026-11-09"}
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_missing_date_returns_400(self):
        self.client.login(username="alice", password=self.password)

        response = self.client.get(reverse("room-schedule", args=[self.room.id]))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("date", response.json())

    def test_invalid_date_returns_400(self):
        self.client.login(username="alice", password=self.password)

        response = self.client.get(
            reverse("room-schedule", args=[self.room.id]), {"date": "not-a-date"}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("date", response.json())

    def test_unknown_room_returns_404(self):
        self.client.login(username="alice", password=self.password)

        response = self.client.get(reverse("room-schedule", args=[999999]), {"date": "2026-11-09"})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_employee_gets_404_for_inactive_room(self):
        self.client.login(username="alice", password=self.password)

        response = self.client.get(
            reverse("room-schedule", args=[self.inactive_room.id]), {"date": "2026-11-09"}
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_can_view_inactive_room_schedule(self):
        User.objects.create_user(username="admin1", password=self.password, is_staff=True)
        self.client.login(username="admin1", password=self.password)

        response = self.client.get(
            reverse("room-schedule", args=[self.inactive_room.id]), {"date": "2026-11-09"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_schedule_includes_booking_fields_and_is_mine(self):
        self.client.login(username="alice", password=self.password)

        response = self.client.get(
            reverse("room-schedule", args=[self.room.id]), {"date": "2026-11-09"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        entries = {entry["id"]: entry for entry in response.json()}
        own_entry = entries[self.same_day_booking.id]
        self.assertEqual(own_entry["title"], "Sprint planning")
        self.assertEqual(own_entry["booked_by"], "alice")
        self.assertTrue(own_entry["is_mine"])

        others_entry = entries[self.spans_midnight_booking.id]
        self.assertEqual(others_entry["booked_by"], "bob")
        self.assertFalse(others_entry["is_mine"])

    def test_booking_spanning_midnight_jst_appears_on_both_days(self):
        self.client.login(username="alice", password=self.password)

        day_one = self.client.get(
            reverse("room-schedule", args=[self.room.id]), {"date": "2026-11-09"}
        )
        day_two = self.client.get(
            reverse("room-schedule", args=[self.room.id]), {"date": "2026-11-10"}
        )

        day_one_ids = {entry["id"] for entry in day_one.json()}
        day_two_ids = {entry["id"] for entry in day_two.json()}
        self.assertIn(self.spans_midnight_booking.id, day_one_ids)
        self.assertIn(self.spans_midnight_booking.id, day_two_ids)

    def test_same_day_booking_does_not_appear_on_adjacent_day(self):
        self.client.login(username="alice", password=self.password)

        response = self.client.get(
            reverse("room-schedule", args=[self.room.id]), {"date": "2026-11-10"}
        )

        ids = {entry["id"] for entry in response.json()}
        self.assertNotIn(self.same_day_booking.id, ids)


class AdminBookingListTests(APITestCase):
    def setUp(self):
        self.password = "correct-horse-battery"
        self.admin = User.objects.create_user(
            username="admin1", password=self.password, is_staff=True
        )
        self.alice = User.objects.create_user(username="alice", password=self.password)
        self.bob = User.objects.create_user(username="bob", password=self.password)
        self.room_a = Room.objects.create(name="Falcon", capacity=8, location="3F")
        self.room_b = Room.objects.create(name="Hawk", capacity=4, location="2F")

        self.booking_1 = Booking.objects.create(
            room=self.room_a,
            user=self.alice,
            title="Alice in Falcon",
            start_time=datetime(2026, 11, 9, 1, 0, tzinfo=UTC),
            end_time=datetime(2026, 11, 9, 2, 0, tzinfo=UTC),
        )
        self.booking_2 = Booking.objects.create(
            room=self.room_b,
            user=self.bob,
            title="Bob in Hawk",
            start_time=datetime(2026, 11, 9, 3, 0, tzinfo=UTC),
            end_time=datetime(2026, 11, 9, 4, 0, tzinfo=UTC),
        )
        self.booking_3 = Booking.objects.create(
            room=self.room_a,
            user=self.bob,
            title="Bob in Falcon",
            start_time=datetime(2026, 11, 10, 1, 0, tzinfo=UTC),
            end_time=datetime(2026, 11, 10, 2, 0, tzinfo=UTC),
        )

    def test_anonymous_user_cannot_list_admin_bookings(self):
        response = self.client.get(reverse("admin-booking-list"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_employee_cannot_list_admin_bookings(self):
        self.client.login(username="alice", password=self.password)

        response = self.client.get(reverse("admin-booking-list"))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_sees_all_bookings_with_nested_room_and_user(self):
        self.client.login(username="admin1", password=self.password)

        response = self.client.get(reverse("admin-booking-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(len(body), 3)
        entry = next(item for item in body if item["id"] == self.booking_1.id)
        self.assertEqual(entry["room"], {"id": self.room_a.id, "name": "Falcon"})
        self.assertEqual(entry["user"], {"id": self.alice.id, "username": "alice"})

    def test_filter_by_room(self):
        self.client.login(username="admin1", password=self.password)

        response = self.client.get(reverse("admin-booking-list"), {"room": self.room_a.id})

        ids = {item["id"] for item in response.json()}
        self.assertEqual(ids, {self.booking_1.id, self.booking_3.id})

    def test_filter_by_user(self):
        self.client.login(username="admin1", password=self.password)

        response = self.client.get(reverse("admin-booking-list"), {"user": self.bob.id})

        ids = {item["id"] for item in response.json()}
        self.assertEqual(ids, {self.booking_2.id, self.booking_3.id})

    def test_filter_by_date(self):
        self.client.login(username="admin1", password=self.password)

        response = self.client.get(reverse("admin-booking-list"), {"date": "2026-11-09"})

        ids = {item["id"] for item in response.json()}
        self.assertEqual(ids, {self.booking_1.id, self.booking_2.id})

    def test_filters_are_combinable(self):
        self.client.login(username="admin1", password=self.password)

        response = self.client.get(
            reverse("admin-booking-list"),
            {"room": self.room_a.id, "user": self.bob.id},
        )

        ids = {item["id"] for item in response.json()}
        self.assertEqual(ids, {self.booking_3.id})

    def test_invalid_date_filter_returns_400(self):
        self.client.login(username="admin1", password=self.password)

        response = self.client.get(reverse("admin-booking-list"), {"date": "not-a-date"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_uses_constant_query_count_regardless_of_row_count(self):
        self.client.login(username="admin1", password=self.password)

        with self.assertNumQueries(3):
            self.client.get(reverse("admin-booking-list"))

        for i in range(5):
            Booking.objects.create(
                room=self.room_a,
                user=self.alice,
                title=f"Extra {i}",
                start_time=datetime(2026, 11, 11, i, 0, tzinfo=UTC),
                end_time=datetime(2026, 11, 11, i, 30, tzinfo=UTC),
            )

        with self.assertNumQueries(3):
            self.client.get(reverse("admin-booking-list"))


class AdminBookingDeleteTests(APITestCase):
    def setUp(self):
        self.password = "correct-horse-battery"
        self.admin = User.objects.create_user(
            username="admin1", password=self.password, is_staff=True
        )
        self.alice = User.objects.create_user(username="alice", password=self.password)
        self.room = Room.objects.create(name="Falcon", capacity=8, location="3F")
        self.booking = Booking.objects.create(
            room=self.room,
            user=self.alice,
            title="Sprint planning",
            start_time=timezone.now() + timedelta(hours=2),
            end_time=timezone.now() + timedelta(hours=3),
        )

    def test_anonymous_user_cannot_delete(self):
        response = self.client.delete(reverse("admin-booking-detail", args=[self.booking.id]))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_employee_cannot_delete_others_booking(self):
        self.client.login(username="alice", password=self.password)

        response = self.client.delete(reverse("admin-booking-detail", args=[self.booking.id]))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_delete_any_booking(self):
        self.client.login(username="admin1", password=self.password)

        response = self.client.delete(reverse("admin-booking-detail", args=[self.booking.id]))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Booking.objects.filter(pk=self.booking.pk).exists())

    def test_unknown_booking_returns_404(self):
        self.client.login(username="admin1", password=self.password)

        response = self.client.delete(reverse("admin-booking-detail", args=[999999]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
