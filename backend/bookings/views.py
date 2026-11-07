from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, mixins, serializers
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from bookings.models import Booking, Room
from bookings.serializers import (
    AdminBookingSerializer,
    BookingSerializer,
    RoomScheduleEntrySerializer,
    RoomSerializer,
    ScheduleDateSerializer,
)
from bookings.utils import local_day_range_utc


class RoomListCreateView(mixins.ListModelMixin, mixins.CreateModelMixin, generics.GenericAPIView):
    serializer_class = RoomSerializer
    pagination_class = None

    def get_queryset(self):
        if self.request.user.is_staff:
            return Room.objects.all()
        return Room.objects.filter(is_active=True)

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class RoomDetailView(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, generics.GenericAPIView):
    serializer_class = RoomSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return Room.objects.all()
        return Room.objects.filter(is_active=True)

    def get_permissions(self):
        # PUT/DELETE have no handler below and always 405 (BR-8), regardless
        # of who's asking, so they must not be blocked by auth/permissions.
        if self.request.method in ("PUT", "DELETE"):
            return [AllowAny()]
        if self.request.method == "PATCH":
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class BookingListCreateView(
    mixins.ListModelMixin, mixins.CreateModelMixin, generics.GenericAPIView
):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        now = timezone.now()
        qs = Booking.objects.filter(user=self.request.user).select_related("room")
        if self.request.query_params.get("past") == "true":
            qs = qs.filter(end_time__lt=now)
        else:
            qs = qs.filter(end_time__gte=now)
        return qs.order_by("start_time")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class BookingDetailView(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    generics.GenericAPIView,
):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user).select_related("room")

    def perform_update(self, serializer):
        if serializer.instance.start_time <= timezone.now():
            raise serializers.ValidationError(
                {"detail": "BR-7: booking has already started and is read-only."}
            )
        serializer.save()

    def perform_destroy(self, instance):
        if instance.start_time <= timezone.now():
            raise serializers.ValidationError(
                {"detail": "BR-7: booking has already started and is read-only."}
            )
        instance.delete()

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class RoomScheduleView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=RoomScheduleEntrySerializer(many=True))
    def get(self, request, pk):
        if request.user.is_staff:
            room = get_object_or_404(Room, pk=pk)
        else:
            room = get_object_or_404(Room, pk=pk, is_active=True)

        query = ScheduleDateSerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        day_start_utc, day_end_utc = local_day_range_utc(query.validated_data["date"])

        bookings = (
            Booking.objects.filter(
                room=room, start_time__lt=day_end_utc, end_time__gt=day_start_utc
            )
            .select_related("user")
            .order_by("start_time")
        )
        entries = [
            {
                "id": booking.id,
                "title": booking.title,
                "start_time": booking.start_time,
                "end_time": booking.end_time,
                "booked_by": booking.user.username,
                "is_mine": booking.user_id == request.user.id,
            }
            for booking in bookings
        ]
        return Response(RoomScheduleEntrySerializer(entries, many=True).data)


class AdminBookingListView(generics.ListAPIView):
    serializer_class = AdminBookingSerializer
    permission_classes = [IsAdminUser]
    pagination_class = None

    def get_queryset(self):
        qs = Booking.objects.select_related("room", "user").order_by("start_time")

        room_id = self.request.query_params.get("room")
        if room_id:
            qs = qs.filter(room_id=room_id)

        user_id = self.request.query_params.get("user")
        if user_id:
            qs = qs.filter(user_id=user_id)

        date_str = self.request.query_params.get("date")
        if date_str:
            query = ScheduleDateSerializer(data={"date": date_str})
            query.is_valid(raise_exception=True)
            day_start_utc, day_end_utc = local_day_range_utc(query.validated_data["date"])
            qs = qs.filter(start_time__lt=day_end_utc, end_time__gt=day_start_utc)

        return qs


class AdminBookingDetailView(mixins.DestroyModelMixin, generics.GenericAPIView):
    queryset = Booking.objects.all()
    serializer_class = AdminBookingSerializer

    def get_permissions(self):
        # GET/PATCH/PUT have no handler below and always 405, regardless of
        # who's asking, so they must not be blocked by auth/permissions.
        if self.request.method == "DELETE":
            return [IsAdminUser()]
        return [AllowAny()]

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
