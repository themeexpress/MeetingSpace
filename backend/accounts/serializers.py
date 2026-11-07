from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from accounts.exceptions import SelfDemotionError


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "is_staff"]


class AdminUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, trim_whitespace=False)
    upcoming_booking_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "is_staff",
            "is_active",
            "date_joined",
            "last_login",
            "upcoming_booking_count",
            "password",
        ]
        read_only_fields = ["id", "date_joined", "last_login"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cancelled_bookings_count = None
        if self.instance is not None:
            self.fields["username"].read_only = True

    def get_upcoming_booking_count(self, obj) -> int:
        return obj.bookings.filter(end_time__gte=timezone.now()).count()

    def validate_password(self, value):
        user = self.instance or User(username=self.initial_data.get("username", ""))
        try:
            validate_password(value, user=user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value

    def validate(self, attrs):
        if self.instance is None and "password" not in attrs:
            raise serializers.ValidationError({"password": ["This field is required."]})

        request = self.context.get("request")
        if self.instance is not None and request is not None and self.instance == request.user:
            if attrs.get("is_active") is False or attrs.get("is_staff") is False:
                raise SelfDemotionError()

        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        deactivating = validated_data.get("is_active") is False and instance.is_active

        with transaction.atomic():
            if password:
                instance.set_password(password)
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            cancelled_count = 0
            if deactivating:
                future_bookings = instance.bookings.filter(end_time__gte=timezone.now())
                cancelled_count = future_bookings.count()
                future_bookings.delete()

        if deactivating:
            self._cancelled_bookings_count = cancelled_count
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if self._cancelled_bookings_count is not None:
            data["cancelled_bookings_count"] = self._cancelled_bookings_count
        return data


class DetailSerializer(serializers.Serializer):
    detail = serializers.CharField()


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(trim_whitespace=False)

    def validate(self, attrs):
        user = authenticate(username=attrs["username"], password=attrs["password"])
        if user is None:
            raise serializers.ValidationError("Unable to log in with provided credentials.")
        attrs["user"] = user
        return attrs
