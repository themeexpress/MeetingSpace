from rest_framework import serializers

from bookings.models import Room


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ["id", "name", "capacity", "location", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]
