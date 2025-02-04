from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from rest_framework.test import APIClient

from tests.generics import GenericTest
from tests.mixins import (
    AssertContentKeysMixin,
    AssertPaginatedResponseMixin,
    AssertResponseMixin,
    CheckUserDataMixin,
    IterableFollowingRelationsMixin,
    RegisterObjectsMixin,
    SendEndpointDetailRequestMixin,
)
from tests.services import FollowTestMode, FollowTestService

User = get_user_model()


def change_user_comments_private_status(client: APIClient, user: User, status: str) -> None:
    data = {"comments_private_status": status}
    client.force_authenticate(user)
    client.patch(reverse_lazy("users:account-update"), data=data)


__all__ = [
    "GenericTest",
    "FollowTestService",
    "FollowTestMode",
    "RegisterObjectsMixin",
    "IterableFollowingRelationsMixin",
    "AssertPaginatedResponseMixin",
    "AssertResponseMixin",
    "AssertContentKeysMixin",
    "SendEndpointDetailRequestMixin",
    "CheckUserDataMixin",
    "change_user_comments_private_status",
]
