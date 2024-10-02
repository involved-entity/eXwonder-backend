import pytz
from datetime import datetime
import typing


def datetime_to_timezone(dt: datetime, timezone: str, attribute_name: typing.Optional[str] = 'time_added') -> typing.Dict:
    dt = pytz.timezone(timezone).localize(datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second))
    return {
        attribute_name: (dt + dt.utcoffset()).strftime("%d/%m/%Y %H:%M"),
        "timezone": timezone
    }
