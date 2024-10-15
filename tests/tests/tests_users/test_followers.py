import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from tests import FollowTestMode, FollowTestService, GenericTest

User = get_user_model()
pytestmark = [pytest.mark.django_db]


class TestFollowersOfUser(GenericTest):
    endpoint_follow = "users:followings-list"
    endpoint_list = "users:followers-list"

    list_tests_count = 5

    service = FollowTestService(
        endpoint_follow,
        endpoint_list,
        list_tests_count,
        FollowTestMode.FOLLOWERS
    )

    def test_followers_of_user(self, api_client):
        super().make_test(api_client)

    def case_test(self, client: APIClient, instance: User) -> None:
        self.service.make_follow_test(client)
