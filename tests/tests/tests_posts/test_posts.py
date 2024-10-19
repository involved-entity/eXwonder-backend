import typing

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from posts.models import Post
from tests import AssertPaginatedResponseMixin, AssertResponseMixin, GenericTest

User = get_user_model()
pytestmark = [pytest.mark.django_db]

POST_NEEDED_FIELDS = "id", "author", "signature", "time_added", "images", "likes_count", "comments_count"


class TestPostsCreation(GenericTest):
    endpoint_list = "posts:posts-list"
    endpoint_detail = "posts:posts-detail"

    def test_posts_creation(self, api_client):
        super().make_test(api_client)

    def case_test(self, client: APIClient, instance: User) -> None:
        self.register_post(client, instance)


class TestPostsUser(AssertPaginatedResponseMixin, GenericTest):
    endpoint_list = "posts:posts-list"
    endpoint_detail = "posts:posts-detail"

    def test_posts_user(self, api_client):
        super().make_test(api_client)

    def case_test(self, client: APIClient, instance: User) -> Response:
        author = self.register_users(client, 1)[0]

        for _ in range(self.list_tests_count):
            self.register_post(client, author)

        client.force_authenticate(instance)
        url = f"{reverse_lazy(self.endpoint_list)}?user={author.username}"
        return client.get(url)

    def assert_case_test(self, response: Response, *args) -> None:
        content = self.assert_paginated_response(response)
        for post in content["results"]:
            self.assert_keys(post, POST_NEEDED_FIELDS)
            assert len(post["images"]) == 2


class TestPostsRetrieve(AssertResponseMixin, GenericTest):
    endpoint_list = "posts:posts-list"
    endpoint_detail = "posts:posts-detail"

    def test_posts_retrieve(self, api_client):
        super().make_test(api_client)

    def case_test(self, client: APIClient, instance: User) -> typing.Tuple[Response, Post, User]:
        post = self.register_post(client, instance)   # noqa
        client.force_authenticate(instance)
        return client.get(reverse_lazy(self.endpoint_detail, kwargs={"id": post.id})), post, instance   # noqa

    def assert_case_test(self, response: Response, *args) -> None:
        content = self.assert_response(response, needed_keys=POST_NEEDED_FIELDS)
        assert content["id"] == args[0].id
        assert content["author"]["id"] == args[1].id
        assert content["signature"] == args[0].signature
        assert len(content["images"]) == 2


class TestPostsDelete(GenericTest):
    endpoint_list = "posts:posts-list"
    endpoint_detail = "posts:posts-detail"

    def test_posts_delete(self, api_client):
        super().make_test(api_client)

    def case_test(self, client: APIClient, instance: User) -> Response:
        post_id = self.register_post(client, instance).id   # noqa
        client.force_authenticate(instance)
        return client.delete(reverse_lazy(self.endpoint_detail, kwargs={"id": post_id}))   # noqa

    def assert_case_test(self, response: Response, *args) -> None:
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Post.objects.count() == 0   # noqa
