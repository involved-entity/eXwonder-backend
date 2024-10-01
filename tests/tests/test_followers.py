import json
import typing

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from rest_framework import status
from rest_framework.test import APIClient

from tests import register_users
from tests.factories import UserFactory

User = get_user_model()
pytestmark = [pytest.mark.django_db]


class TestFollowers(object):
    endpoint_follow = "api:follows-list"
    endpoint_list = "api:followers-list"

    tests_count = 2
    list_tests_count = 5

    def test_follows_of_user(self, api_client: typing.Type[APIClient], user_factory: typing.Type[UserFactory]) -> None:
        client = api_client()
        for _ in range(self.tests_count):
            user = User.objects.get(username=register_users(client, user_factory, 1)[0].username)
            followings = register_users(client, user_factory, self.list_tests_count)
            url = reverse_lazy(self.endpoint_follow)

            for index, following in enumerate(followings):
                client.force_authenticate(User.objects.get(username=following.username))
                response = client.post(url, data={"following": user.pk})
                assert response.status_code == status.HTTP_201_CREATED
                assert user.followers.count() == index + 1

            url = reverse_lazy(self.endpoint_list)
            client.force_authenticate(user)
            response = client.get(url)
            assert response.status_code == status.HTTP_200_OK
            content = json.loads(response.content)
            assert "count" in list(content.keys()) and content["count"] == self.list_tests_count
            assert len(content["results"]) == self.list_tests_count
