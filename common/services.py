import typing
from datetime import datetime

import pytz
from django.utils.timesince import timesince


def datetime_to_timezone(
    dt: datetime, timezone: str, attribute_name: typing.Optional[str] = "time_added"
) -> typing.Dict:
    dt = pytz.timezone(timezone).localize(datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second))
    return {attribute_name: timesince(dt + dt.utcoffset()), "timezone": timezone}
