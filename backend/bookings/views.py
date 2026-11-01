from django.utils import timezone
from rest_framework import generics, mixins, serializers
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated

from bookings.models import Booking, Room
from bookings.serializers import BookingSerializer, RoomSerializer


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
