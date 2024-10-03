import json
import typing

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from rest_framework import status
from rest_framework.test import APIClient

from posts.models import Post, Comment
from tests import register_post, register_users
from tests.factories import PostFactory, UserFactory, CommentFactory

User = get_user_model()
pytestmark = [pytest.mark.django_db]


class TestComments(object):
    endpoint_list = "posts:comments-list"
    endpoint_detail = "posts:comments-detail"
    endpoint_post_delete = "posts:posts-detail"

    tests_count = 2
    list_test_count = 5

    def __register_comment(self, client: APIClient, comment_factory: typing.Type[CommentFactory],
                           post_or_factory: typing.Type[PostFactory], author: User) -> User:
        user = User.objects.get(username=author.username)
        if post_or_factory.__class__ == Post:
            post_id = post_or_factory.pk   # noqa
        elif post_or_factory == PostFactory:
            signature = register_post(client, post_or_factory, user)
            post_id = Post.objects.get(signature=signature).id   # noqa
        client.force_authenticate(user)
        data = {
            "post_id": post_id,   # noqa
            "comment": comment_factory.stub().comment
        }
        response = client.post(reverse_lazy(self.endpoint_list), data=data)
        client.force_authenticate()
        assert response.status_code == status.HTTP_201_CREATED
        return user

    def test_comments_creation(self, api_client: typing.Type[APIClient], user_factory: typing.Type[UserFactory],
                               post_factory: typing.Type[PostFactory], comment_factory: typing.Type[CommentFactory]) \
            -> None:
        client = api_client()
        users = register_users(client, user_factory, self.tests_count)

        for user in users:
            self.__register_comment(client, comment_factory, post_factory, user)

    def test_comments_delete(self, api_client: typing.Type[APIClient], user_factory: typing.Type[UserFactory],
                             post_factory: typing.Type[PostFactory], comment_factory: typing.Type[CommentFactory]) \
            -> None:
        client = api_client()
        users = register_users(client, user_factory, self.tests_count)

        for user in users:
            user = self.__register_comment(client, comment_factory, post_factory, user)
            client.force_authenticate(user)
            response = client.delete(reverse_lazy(self.endpoint_detail, kwargs={"id": Comment.objects.get(author=user).pk}))   # noqa
            assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_comments_of_post(self, api_client: typing.Type[APIClient], user_factory: typing.Type[UserFactory],
                           post_factory: typing.Type[PostFactory], comment_factory: typing.Type[CommentFactory]) \
            -> None:
        client = api_client()
        users = register_users(client, user_factory, self.tests_count)

        for user in users:
            user = User.objects.get(username=user.username)
            post = Post.objects.get(signature=register_post(client, post_factory, user))   # noqa
            comment_authors = register_users(client, user_factory, self.list_test_count)

            for author in comment_authors:
                self.__register_comment(client, comment_factory, post, author)

            client.force_authenticate(user)
            response = client.get(f"{reverse_lazy(self.endpoint_list)}?post_id={post.id}")
            assert response.status_code == status.HTTP_200_OK
            assert json.loads(response.content)["count"] == self.list_test_count
            client.delete(reverse_lazy(self.endpoint_post_delete, kwargs={"id": post.id}))
