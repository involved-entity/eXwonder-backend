import typing

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from tests import FollowTestMode, FollowTestService
from tests.factories import UserFactory

User = get_user_model()
pytestmark = [pytest.mark.django_db]


class TestFollowers(object):
    endpoint_follow = "api:followings-list"
    endpoint_list = "api:followers-list"

    tests_count = 2
    list_tests_count = 5

    def test_followers_of_user(self, api_client: typing.Type[APIClient], user_factory: typing.Type[UserFactory]) -> None:
        client = api_client()
        service = FollowTestService(
            self.endpoint_follow,
            self.endpoint_list,
            self.list_tests_count,
            FollowTestMode.FOLLOWERS
        )
        for _ in range(self.tests_count):
            service.make_follow_test(client, user_factory)
