from django.urls import path

from bookings.views import (
    AdminBookingDetailView,
    AdminBookingListView,
    BookingDetailView,
    BookingListCreateView,
    RoomDetailView,
    RoomListCreateView,
    RoomScheduleView,
)

urlpatterns = [
    path("rooms/", RoomListCreateView.as_view(), name="room-list"),
    path("rooms/<int:pk>/", RoomDetailView.as_view(), name="room-detail"),
    path("rooms/<int:pk>/schedule/", RoomScheduleView.as_view(), name="room-schedule"),
    path("bookings/", BookingListCreateView.as_view(), name="booking-list"),
    path("bookings/<int:pk>/", BookingDetailView.as_view(), name="booking-detail"),
    path("admin/bookings/", AdminBookingListView.as_view(), name="admin-booking-list"),
    path(
        "admin/bookings/<int:pk>/",
        AdminBookingDetailView.as_view(),
        name="admin-booking-detail",
    ),
]
