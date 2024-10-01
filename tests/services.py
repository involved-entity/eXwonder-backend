import json
import typing
from enum import StrEnum

from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from rest_framework import status
from rest_framework.test import APIClient

from tests.factories import UserFactory

User = get_user_model()
BatchCreateUsers = typing.List
BatchStubUsers = typing.List

REGISTER_USERS_ENDPOINT = "api:account-list"


class FollowTestMode(StrEnum):
    FOLLOWERS = "followers"
    FOLLOWINGS = "followings"


class FollowTestService(object):
    def __init__(self, endpoint_follow: str, endpoint_list: str, list_tests_count: int, mode: FollowTestMode):
        self.endpoint_follow = endpoint_follow
        self.endpoint_list = endpoint_list
        self.list_tests_count = list_tests_count
        self.mode = mode

    def make_follow_test(self, client: APIClient, user_factory: typing.Type[UserFactory]) \
            -> None:
        user = User.objects.get(username=register_users(client, user_factory, 1)[0].username)
        followings = register_users(client, user_factory, self.list_tests_count)
        url = reverse_lazy(self.endpoint_follow)

        for index, following in enumerate(followings):
            auth_user = User.objects.get(username=following.username) if self.mode == FollowTestMode.FOLLOWERS else user
            client.force_authenticate(auth_user)
            following = user.pk \
                if self.mode == FollowTestMode.FOLLOWERS else User.objects.get(username=following.username).pk
            response = client.post(url, data={"following": following})
            assert response.status_code == status.HTTP_201_CREATED
            assert user.followers.count() == index + 1 \
                if self.mode == FollowTestMode.FOLLOWERS else user.following.count() == index + 1

        url = reverse_lazy(self.endpoint_list)
        client.force_authenticate(user)
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        content = json.loads(response.content)
        assert "count" in list(content.keys()) and content["count"] == self.list_tests_count
        assert len(content["results"]) == self.list_tests_count


def get_users_for_test(user_factory: typing.Type[UserFactory], users_count: int, stub: bool = False) \
        -> BatchCreateUsers | BatchStubUsers:
    return user_factory.create_batch(users_count) if not stub else user_factory.stub_batch(users_count)


def register_users(client: APIClient, user_factory: typing.Type[UserFactory], users_count: int) -> BatchStubUsers:
    users_data = get_users_for_test(user_factory, users_count, stub=True)
    for user_data in users_data:
        data = {
            "username": user_data.username,
            "email": user_data.email,
            "password": user_data.password,
        }
        response = client.post(reverse_lazy(REGISTER_USERS_ENDPOINT), data=data)
        assert response.status_code == status.HTTP_201_CREATED
    return users_data
