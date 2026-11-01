from django.urls import path

from bookings.views import (
    BookingDetailView,
    BookingListCreateView,
    RoomDetailView,
    RoomListCreateView,
)

urlpatterns = [
    path("rooms/", RoomListCreateView.as_view(), name="room-list"),
    path("rooms/<int:pk>/", RoomDetailView.as_view(), name="room-detail"),
    path("bookings/", BookingListCreateView.as_view(), name="booking-list"),
    path("bookings/<int:pk>/", BookingDetailView.as_view(), name="booking-detail"),
]
