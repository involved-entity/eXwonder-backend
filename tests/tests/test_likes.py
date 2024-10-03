import json
import typing

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from rest_framework import status
from rest_framework.test import APIClient

from posts.models import Post
from tests import register_post, register_users
from tests.factories import PostFactory, UserFactory

User = get_user_model()
pytestmark = [pytest.mark.django_db]


class TestLikes(object):
    endpoint_list = "posts:likes-list"

    tests_count = 2

    def test_likes_creation(self, api_client: typing.Type[APIClient], user_factory: typing.Type[UserFactory],
                            post_factory: typing.Type[PostFactory]) -> None:
        client = api_client()
        users = register_users(client, user_factory, self.tests_count)

        for user in users:
            user = User.objects.get(username=user.username)
            signature = register_post(client, post_factory, user)
            data = {"id": Post.objects.get(signature=signature).id}   # noqa
            client.force_authenticate(user)
            response = client.post(reverse_lazy(self.endpoint_list), data=data)
            assert response.status_code == status.HTTP_201_CREATED
