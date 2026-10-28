from django.urls import path

from bookings.views import RoomDetailView, RoomListCreateView

urlpatterns = [
    path("rooms/", RoomListCreateView.as_view(), name="room-list"),
    path("rooms/<int:pk>/", RoomDetailView.as_view(), name="room-detail"),
]
