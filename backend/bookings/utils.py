from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings


def local_day_range_utc(day):
    """UTC [start, end) for a calendar day in APP_TIME_ZONE."""
    tz = ZoneInfo(settings.APP_TIME_ZONE)
    day_start_local = datetime.combine(day, time.min, tzinfo=tz)
    day_end_local = day_start_local + timedelta(days=1)
    return day_start_local.astimezone(UTC), day_end_local.astimezone(UTC)
