import json
import typing
from enum import StrEnum

from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from rest_framework import status
from rest_framework.test import APIClient

from tests import RegisterObjectsMixin
from tests.mixins import BatchStubUsers

User = get_user_model()


class FollowTestMode(StrEnum):
    FOLLOWERS = "followers"
    FOLLOWINGS = "followings"
    FOLLOWINGS_EACH_USER = "followings_each_user"


class FollowTestService(RegisterObjectsMixin):
    endpoint_follow: str = None
    mode: FollowTestMode = None
    __mode_source: FollowTestMode = None

    def __init__(self, endpoint_follow: str, endpoint_list: str, list_tests_count: int, mode: FollowTestMode):
        self.endpoint_follow = endpoint_follow
        self.endpoint_list = endpoint_list
        self.list_tests_count = list_tests_count
        self.mode = FollowTestMode.FOLLOWINGS if mode == FollowTestMode.FOLLOWINGS_EACH_USER else mode
        self.__mode_source = mode

    def __get_registered_user_and_followings(self, client: APIClient) \
            -> typing.Tuple[User, BatchStubUsers]:
        user = self.register_users(client, 1)[0]
        followings = self.register_users(client, self.list_tests_count)
        return user, followings

    def __get_valid_authenticated_client(self, client: APIClient, following: User, user: User) -> APIClient:
        auth_user = following if self.mode == FollowTestMode.FOLLOWERS else user
        client.force_authenticate(auth_user)
        return client

    def __create_and_assert_valid_follow(self, client: APIClient, following: User, index: int, url: str, user: User) \
            -> None:
        following = user if self.mode == FollowTestMode.FOLLOWERS else following
        response = client.post(url, data={"following": following.pk})
        assert response.status_code == status.HTTP_201_CREATED
        assert getattr(user, "followers" if self.mode == FollowTestMode.FOLLOWERS else "following").count() == index + 1

    def __get_valid_assert_follows_url_and_user(self, client: APIClient, user: User) -> typing.Tuple[str, User]:
        match self.__mode_source:
            case FollowTestMode.FOLLOWINGS_EACH_USER:
                url = reverse_lazy(self.endpoint_list, kwargs={"pk": user.pk})
                client.force_authenticate()
                return url, self.register_users(client, 1)
            case _:
                return reverse_lazy(self.endpoint_list), user

    def __check_and_assert_follows(self, client: APIClient, user: User) -> None:
        url, user = self.__get_valid_assert_follows_url_and_user(client, user)

        client.force_authenticate(user)
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        content = json.loads(response.content)
        assert "count" in list(content.keys()) and content["count"] == self.list_tests_count
        assert len(content["results"]) == self.list_tests_count

    def make_follow_test(self, client: APIClient) \
            -> None:
        user, followings = self.__get_registered_user_and_followings(client)
        url = reverse_lazy(self.endpoint_follow)

        for index, following in enumerate(followings):
            client = self.__get_valid_authenticated_client(client, following, user)
            self.__create_and_assert_valid_follow(client, following, index, url, user)

        self.__check_and_assert_follows(client, user)
