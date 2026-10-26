from rest_framework import generics, mixins
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated

from bookings.models import Room
from bookings.serializers import RoomSerializer


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
