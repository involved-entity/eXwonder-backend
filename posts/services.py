import typing
from datetime import datetime
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status
from rest_framework.request import Request
from rest_framework.response import Response
from posts.models import Post

import pytz


class CreateModelCustomMixin(mixins.CreateModelMixin):
    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)   # noqa
        serializer.is_valid(raise_exception=True)
        if request.data.get("post_id", 0) and request.data.get("post_id", 0).isnumeric():
            serializer.save(
                author=request.user,
                post=get_object_or_404(Post, pk=request.data["post_id"])
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)


def datetime_to_timezone(dt: datetime, timezone: str, attribute_name: typing.Optional[str] = 'time_added') \
        -> typing.Dict:
    dt = pytz.timezone(timezone).localize(datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second))
    return {
        attribute_name: (dt + dt.utcoffset()).strftime("%d/%m/%Y %H:%M"),
        "timezone": timezone
    }
