import json
import typing

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from rest_framework import status
import os
from rest_framework.test import APIClient
from django.conf import settings

from posts.models import Post
from tests import register_users
from tests.factories import UserFactory, PostFactory

User = get_user_model()
pytestmark = [pytest.mark.django_db]
PostSignature = str

IMAGES_FOR_TEST_NAMES = [
    "image_1.jpeg",
    "image_2.jpg"
]


class TestPosts(object):
    endpoint_list = "posts:posts-list"
    endpoint_detail = "posts:posts-detail"

    tests_count = 2
    list_tests_count = 2

    def __create_and_assert_post(self, client: APIClient, post_factory: typing.Type[PostFactory], author: User) -> PostSignature:
        client.force_authenticate(author)
        data = {
            "signature": post_factory.stub().signature,
        }
        image_1 = os.path.join(settings.STATICFILES_DIRS[0], settings.TEST_IMAGES_DIR, IMAGES_FOR_TEST_NAMES[0])
        image_2 = os.path.join(settings.STATICFILES_DIRS[0], settings.TEST_IMAGES_DIR, IMAGES_FOR_TEST_NAMES[1])
        with open(image_1, "rb") as image_1:
            with open(image_2, "rb") as image_2:
                data["image1"] = image_1
                data["image2"] = image_2
                response = client.post(reverse_lazy(self.endpoint_list), data=data)
                assert response.status_code == status.HTTP_201_CREATED
        client.force_authenticate()
        return data["signature"]

    def test_posts_creation(self, api_client: typing.Type[APIClient], user_factory: typing.Type[UserFactory],
                            post_factory: typing.Type[PostFactory]) -> None:
        client = api_client()
        users = register_users(client, user_factory, self.tests_count)

        for user in users:
            self.__create_and_assert_post(client, post_factory, User.objects.get(username=user.username))

    def test_posts_users(self, api_client: typing.Type[APIClient], user_factory: typing.Type[UserFactory],
                         post_factory: typing.Type[PostFactory]) -> None:
        client = api_client()
        users = register_users(client, user_factory, self.tests_count)

        for user in users:
            author = User.objects.get(username=register_users(client, user_factory, 1)[0].username)

            for _ in range(self.list_tests_count):
                self.__create_and_assert_post(client, post_factory, author)

            client.force_authenticate(User.objects.get(username=user.username))
            url = f"{reverse_lazy(self.endpoint_list)}?user={author.id}"
            response = client.get(url)
            content = json.loads(response.content)
            assert response.status_code == status.HTTP_200_OK
            assert "count" in list(content.keys()) and content["count"] == self.list_tests_count
            assert len(content["results"]) == self.list_tests_count
            for post in content["results"]:
                assert len(post["images"]) == 2

    def test_posts_retrieve(self, api_client: typing.Type[APIClient], user_factory: typing.Type[UserFactory],
                            post_factory: typing.Type[PostFactory]) -> None:
        client = api_client()
        users = register_users(client, user_factory, self.tests_count)

        for user in users:
            user = User.objects.get(username=user.username)
            signature = self.__create_and_assert_post(client, post_factory, user)
            post = Post.objects.filter()[0]
            client.force_authenticate(user)
            response = client.get(reverse_lazy(self.endpoint_detail, kwargs={"id": post.id}))
            content = json.loads(response.content)
            assert response.status_code == status.HTTP_200_OK
            assert content["id"] == post.id
            assert content["signature"] == signature

    def test_posts_delete(self, api_client: typing.Type[APIClient], user_factory: typing.Type[UserFactory],
                          post_factory: typing.Type[PostFactory]) -> None:
        client = api_client()
        users = register_users(client, user_factory, self.tests_count)

        for user in users:
            user = User.objects.get(username=user.username)
            signature = self.__create_and_assert_post(client, post_factory, user)
            post = Post.objects.filter()[0]
            client.force_authenticate(user)
            assert post.signature == signature
            response = client.delete(reverse_lazy(self.endpoint_detail, kwargs={"id": post.id}))
            assert response.status_code == status.HTTP_204_NO_CONTENT
            posts = Post.objects.filter().count()
            assert posts == 0
