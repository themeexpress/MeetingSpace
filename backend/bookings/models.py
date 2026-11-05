from django.conf import settings
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateTimeRangeField, RangeBoundary, RangeOperators
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class TsTzRange(models.Func):
    function = "TSTZRANGE"
    output_field = DateTimeRangeField()


class Room(models.Model):
    name = models.CharField(max_length=100, unique=True)
    capacity = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    location = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Room"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(capacity__gte=1) & models.Q(capacity__lte=100),
                name="room_capacity_between_1_and_100",
            ),
        ]

    def __str__(self):
        return self.name


class Booking(models.Model):
    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name="bookings")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="bookings"
    )
    title = models.CharField(max_length=120)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_time__gt=models.F("start_time")),
                name="booking_end_after_start",
            ),
            # Race condition: two requests for the same room/time can both pass
            # the serializer's overlap check before either commits (see ADR-2).
            # This constraint is the actual source of truth, enforced atomically
            # by Postgres at commit time; a violation raises IntegrityError,
            # which the view catches and turns into a 409 response.
            ExclusionConstraint(
                name="booking_no_overlapping_time_ranges",
                expressions=[
                    ("room", RangeOperators.EQUAL),
                    (TsTzRange("start_time", "end_time", RangeBoundary()), RangeOperators.OVERLAPS),
                ],
            ),
        ]
        indexes = [
            models.Index(fields=["room", "start_time"], name="booking_room_start_idx"),
        ]

    def __str__(self):
        return f"{self.title} ({self.room} @ {self.start_time})"
