import typing

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from posts.models import Comment, Post
from tests import AssertPaginatedResponseMixin, GenericTest, change_user_comments_private_status
from users.models import ExwonderUser

User = get_user_model()
pytestmark = [pytest.mark.django_db]


class TestCommentsCreation(GenericTest):
    endpoint_list = "posts:comments-list"
    endpoint_detail = "posts:comments-detail"

    def test_comments_creation(self, api_client):
        super().make_test(api_client)

    def case_test(self, client: APIClient, instance: User) -> None:
        self.register_comment(client, instance)


class TestCommentsPrivateStatus(GenericTest):
    endpoint_list = "users:followings-list"

    def test_comments_private_status(self, api_client):
        super().make_test(api_client)

    def case_test(self, client: APIClient, instance: User) -> None:
        user = self.register_users(client, 1)[0]
        post = self.register_post(client, instance)

        self.register_comment(client, user, post=post)

        change_user_comments_private_status(client, instance, ExwonderUser.CommentsPrivateStatus.FOLLOWERS)
        self.register_comment(client, user, post=post, response_status=status.HTTP_400_BAD_REQUEST)

        client.force_authenticate(user)
        response = client.post(reverse_lazy(self.endpoint_list), data={"following": instance.pk})
        assert response.status_code == status.HTTP_201_CREATED
        self.register_comment(client, user, post=post)

        change_user_comments_private_status(client, instance, ExwonderUser.CommentsPrivateStatus.NONE)
        self.register_comment(client, user, post=post, response_status=status.HTTP_400_BAD_REQUEST)


class TestCommentsDelete(GenericTest):
    endpoint_list = "posts:comments-list"
    endpoint_detail = "posts:comments-detail"

    def test_comments_delete(self, api_client):
        super().make_test(api_client)

    def case_test(self, client: APIClient, instance: User) -> None:
        comment = self.register_comment(client, instance)
        client.force_authenticate(instance)
        return client.delete(reverse_lazy(self.endpoint_detail, kwargs={"id": comment.pk}))

    def assert_case_test(self, response: Response, *args) -> None:
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Comment.objects.count() == 0  # noqa


class TestCommentsOfPost(AssertPaginatedResponseMixin, GenericTest):
    endpoint_list = "posts:comments-list"
    endpoint_detail = "posts:comments-detail"
    endpoint_post_delete = "posts:posts-detail"

    def test_comments_of_post(self, api_client):
        super().make_test(api_client)

    def case_test(self, client: APIClient, instance: User) -> typing.Tuple[Response, Post]:
        post = self.register_post(client, instance)
        comment_authors = self.register_users(client, self.list_tests_count)

        for author in comment_authors:
            self.register_comment(client, author, post)

        client.force_authenticate(instance)
        return client.get(f"{reverse_lazy(self.endpoint_list)}?post_id={post.id}"), post  # noqa

    def assert_case_test(self, response: Response, *args) -> None:
        content = self.assert_paginated_response(response)
        for result in content["results"]:
            self.assert_keys(result, ("id", "author", "post", "comment"))

    def after_assert(self, client: APIClient, *args) -> None:
        client.delete(reverse_lazy(self.endpoint_post_delete, kwargs={"id": args[0].id}))
