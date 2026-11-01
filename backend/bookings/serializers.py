from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from bookings.models import Booking, Room


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ["id", "name", "capacity", "location", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]


def _is_on_quarter_hour(value):
    return value.second == 0 and value.microsecond == 0 and value.minute % 15 == 0


class BookingSerializer(serializers.ModelSerializer):
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all())

    class Meta:
        model = Booking
        fields = ["id", "room", "title", "start_time", "end_time", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["room"] = {"id": instance.room_id, "name": instance.room.name}
        return data

    def validate_room(self, room):
        if not room.is_active:
            raise serializers.ValidationError("BR-5: room is not active.")
        return room

    def validate_start_time(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("BR-2: cannot start in the past.")
        if not _is_on_quarter_hour(value):
            raise serializers.ValidationError("BR-4: start_time must fall on a 15-minute boundary.")
        return value

    def validate_end_time(self, value):
        if not _is_on_quarter_hour(value):
            raise serializers.ValidationError("BR-4: end_time must fall on a 15-minute boundary.")
        return value

    def validate(self, attrs):
        start_time = attrs.get("start_time", getattr(self.instance, "start_time", None))
        end_time = attrs.get("end_time", getattr(self.instance, "end_time", None))

        if start_time and end_time:
            if end_time <= start_time:
                raise serializers.ValidationError(
                    {"end_time": ["BR-1: end_time must be after start_time."]}
                )
            duration = end_time - start_time
            if duration < timedelta(minutes=15) or duration > timedelta(hours=4):
                raise serializers.ValidationError(
                    {"end_time": ["BR-3: duration must be between 15 minutes and 4 hours."]}
                )

        return attrs
