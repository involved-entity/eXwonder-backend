import json
import typing

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from rest_framework import status
import os
from rest_framework.test import APIClient
from django.conf import settings

from tests import register_users
from tests.factories import UserFactory, PostFactory

User = get_user_model()
pytestmark = [pytest.mark.django_db]

IMAGES_FOR_TEST_NAMES = [
    "image_1.jpeg",
    "image_2.jpg"
]


class TestPosts(object):
    endpoint_list = "posts:posts-list"

    tests_count = 2

    def test_posts_creation(self, api_client: typing.Type[APIClient], user_factory: typing.Type[UserFactory],
                            post_factory: typing.Type[PostFactory]) -> None:
        client = api_client()
        users = register_users(client, user_factory, self.tests_count)

        for user in users:
            client.force_authenticate(User.objects.get(username=user.username))
            data = {
                "signature": post_factory.stub().signature,
            }
            image_1 = os.path.join(settings.STATICFILES_DIRS[0], settings.TEST_IMAGES_DIR, IMAGES_FOR_TEST_NAMES[0])
            image_2 = os.path.join(settings.STATICFILES_DIRS[0], settings.TEST_IMAGES_DIR, IMAGES_FOR_TEST_NAMES[1])
            with open(image_1, "rb") as image_1:
                with open(image_2, "rb") as image_2:
                    data["image_1"] = image_1
                    data["image_2"] = image_2
                    response = client.post(reverse_lazy(self.endpoint_list), data=data)
                    assert response.status_code == status.HTTP_201_CREATED
