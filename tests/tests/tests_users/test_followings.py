import typing

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from tests import FollowTestMode, FollowTestService, GenericTest, IterableFollowingRelationsMixin

User = get_user_model()
pytestmark = [pytest.mark.django_db]

UserFollower = UserFollowing = User
UsersWithFollowsRelations = typing.List[typing.Tuple[UserFollower, UserFollowing]]


class TestFollowingsCreation(IterableFollowingRelationsMixin, GenericTest):
    endpoint_list = "users:followings-list"
    endpoint_disfollow = "users:followings-disfollow"

    def test_followings_creation(self, api_client):
        super().make_test(api_client)


class TestFollowingsDisfollow(IterableFollowingRelationsMixin, GenericTest):
    endpoint_list = "users:followings-list"
    endpoint_disfollow = "users:followings-disfollow"

    def test_followings_disfollow(self, api_client):
        super().make_test(api_client)

    def case_test(self, client: APIClient, instance: typing.Tuple) -> typing.Tuple[Response, User]:
        client.force_authenticate(instance[0])
        return client.post(reverse_lazy(self.endpoint_disfollow), data={"following": instance[1].pk}), instance[0]

    def assert_case_test(self, response: Response, *args) -> None:
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert args[0].following.count() == 0


class TestFollowingsOfUser(GenericTest):
    endpoint_list = "users:followings-list"
    endpoint_disfollow = "users:followings-disfollow"
    endpoint_user = "users:followings-user"

    list_tests_count = 5

    service = FollowTestService(
        endpoint_list,
        "users:followings-user",
        list_tests_count,
        FollowTestMode.FOLLOWINGS
    )

    def test_followings_of_user(self, api_client):
        super().make_test(api_client)

    def case_test(self, client: APIClient, instance: User) -> None:
        self.service.make_follow_test(client)


class TestFollowingsOfEachUser(GenericTest):
    endpoint_list = "users:followings-list"
    endpoint_disfollow = "users:followings-disfollow"
    endpoint_user = "users:followings-user"

    list_tests_count = 5

    service = FollowTestService(
        endpoint_list,
        endpoint_user,
        list_tests_count,
        FollowTestMode.FOLLOWINGS_EACH_USER
    )

    def test_followings_of_each_user(self, api_client):
        super().make_test(api_client)

    def case_test(self, client: APIClient, instance: User) -> None:
        self.service.make_follow_test(client)
