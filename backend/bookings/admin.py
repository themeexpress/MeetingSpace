from django.contrib import admin

from bookings.models import Room


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "capacity", "location", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["name", "location"]
