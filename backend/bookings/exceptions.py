from rest_framework import status
from rest_framework.exceptions import APIException


class BookingConflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "BR-6: room is already booked for part of this time range."
    default_code = "booking_conflict"
