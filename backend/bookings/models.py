from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


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
