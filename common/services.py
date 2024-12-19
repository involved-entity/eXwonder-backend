import typing
from datetime import datetime

import pytz
from django.utils.timesince import timesince


def datetime_to_timezone(
    dt: datetime, timezone: str, attribute_name: typing.Optional[str] = "time_added", to_timesince: bool = True
) -> typing.Dict:
    dt = pytz.timezone(timezone).localize(datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second))
    time = timesince(dt + dt.utcoffset()) if to_timesince else (dt + dt.utcoffset()).strftime("%H:%M %d.%m.%Y")
    return {attribute_name: time, "timezone": timezone}
