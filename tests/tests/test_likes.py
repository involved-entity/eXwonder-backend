import typing

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from rest_framework import status
from rest_framework.test import APIClient

from posts.models import Like, Post
from tests import register_post, register_users
from tests.factories import PostFactory, UserFactory

User = get_user_model()
pytestmark = [pytest.mark.django_db]


class TestLikes(object):
    endpoint_list = "posts:likes-list"
    endpoint_detail = "posts:likes-detail"

    tests_count = 2
    list_test_count = 5

    def __make_like(self, client: APIClient, post_or_factory: typing.Type[PostFactory] | Post,
                    author: User) -> typing.Tuple[User, int]:
        user = User.objects.get(username=author.username)
        if post_or_factory.__class__ == Post:
            post_id = post_or_factory.pk
        elif post_or_factory == PostFactory:
            signature = register_post(client, post_or_factory, user)
            post_id = Post.objects.get(signature=signature).id   # noqa
        data = {"post_id": post_id}   # noqa
        client.force_authenticate(user)
        response = client.post(reverse_lazy(self.endpoint_list), data=data)
        assert response.status_code == status.HTTP_201_CREATED
        client.force_authenticate()
        return user, post_id

    def test_likes_creation(self, api_client: typing.Type[APIClient], user_factory: typing.Type[UserFactory],
                            post_factory: typing.Type[PostFactory]) -> None:
        client = api_client()
        users = register_users(client, user_factory, self.tests_count)

        for user in users:
            self.__make_like(client, post_factory, user)

    def test_likes_delete(self, api_client: typing.Type[APIClient], user_factory: typing.Type[UserFactory],
                          post_factory: typing.Type[PostFactory]) -> None:
        client = api_client()
        users = register_users(client, user_factory, self.tests_count)

        for user in users:
            user, post_id = self.__make_like(client, post_factory, user)
            client.force_authenticate(user)
            response = client.delete(reverse_lazy(self.endpoint_detail, kwargs={"post_id": post_id}))
            assert response.status_code == status.HTTP_204_NO_CONTENT
            assert Like.objects.filter().count() == 0   # noqa
