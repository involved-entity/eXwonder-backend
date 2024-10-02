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
    FOLLOWINGS_EACH_USER = "followings_each_user"


class FollowTestService(object):
    def __init__(self, endpoint_follow: str, endpoint_list: str, list_tests_count: int, mode: FollowTestMode):
        self.endpoint_follow = endpoint_follow
        self.endpoint_list = endpoint_list
        self.list_tests_count = list_tests_count
        self.mode = FollowTestMode.FOLLOWINGS if mode == FollowTestMode.FOLLOWINGS_EACH_USER else mode
        self.__mode_source = mode

    def __get_registered_user_and_followings(self, client: APIClient, user_factory: typing.Type[UserFactory]) \
            -> typing.Tuple[User, BatchStubUsers]:
        user = User.objects.get(username=register_users(client, user_factory, 1)[0].username)
        followings = register_users(client, user_factory, self.list_tests_count)
        return user, followings

    def __get_valid_authenticated_client(self, client: APIClient, following: User, user: User) -> APIClient:
        auth_user = User.objects.get(username=following.username) if self.mode == FollowTestMode.FOLLOWERS else user
        client.force_authenticate(auth_user)
        return client

    def __create_and_assert_valid_follow(self, client: APIClient, following: User, index: int, url: str, user: User) \
            -> None:
        following = user.pk \
            if self.mode == FollowTestMode.FOLLOWERS else User.objects.get(username=following.username).pk
        response = client.post(url, data={"following": following})
        assert response.status_code == status.HTTP_201_CREATED
        assert user.followers.count() == index + 1 \
            if self.mode == FollowTestMode.FOLLOWERS else user.following.count() == index + 1

    def __check_and_assert_follows(self, client: APIClient, user_factory: typing.Type[UserFactory], user: User) -> None:
        match self.__mode_source:
            case FollowTestMode.FOLLOWINGS_EACH_USER:
                url = reverse_lazy(self.endpoint_list, kwargs={"pk": user.pk})
                client.force_authenticate()
                user = User.objects.get(username=register_users(client, user_factory, 1)[0].username)
            case _:
                url = reverse_lazy(self.endpoint_list)

        client.force_authenticate(user)
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        content = json.loads(response.content)
        assert "count" in list(content.keys()) and content["count"] == self.list_tests_count
        assert len(content["results"]) == self.list_tests_count

    def make_follow_test(self, client: APIClient, user_factory: typing.Type[UserFactory]) \
            -> None:
        user, followings = self.__get_registered_user_and_followings(client, user_factory)
        url = reverse_lazy(self.endpoint_follow)

        for index, following in enumerate(followings):
            client = self.__get_valid_authenticated_client(client, following, user)
            self.__create_and_assert_valid_follow(client, following, index, url, user)

        self.__check_and_assert_follows(client, user_factory, user)


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
