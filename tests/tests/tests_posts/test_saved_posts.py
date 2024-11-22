import json

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from posts.models import Saved
from tests import AssertContentKeysMixin, AssertResponseMixin, GenericTest

User = get_user_model()
pytestmark = [pytest.mark.django_db]


class TestSavedCreation(GenericTest):
    endpoint_list = "posts:saved-list"

    def test_saved_creation(self, api_client):
        super().make_test(api_client)

    def case_test(self, client: APIClient, instance: User) -> None:
        self.register_saved_post(client, instance)


class TestSavedPosts(AssertContentKeysMixin, GenericTest):
    endpoint_list = "posts:saved-list"

    def test_saved_posts(self, api_client):
        super().make_test(api_client)

    def case_test(self, client: APIClient, instance: User) -> Response:
        user = self.register_users(client, 1)[0]

        for _ in range(self.list_tests_count):
            self.register_saved_post(client, instance)

        self.register_saved_post(client, user)

        client.force_authenticate(instance)
        return client.get(reverse_lazy(self.endpoint_list))

    def assert_case_test(self, response: Response, *args) -> None:
        content = json.loads(response.content)
        assert response.status_code == status.HTTP_200_OK
        assert content["count"] == self.list_tests_count
        self.assert_keys(content["results"][0], ("likes_count", "comments_count", "is_liked", "is_commented"))


class TestSavedDestroy(AssertResponseMixin, GenericTest):
    endpoint_detail = "posts:saved-detail"

    def test_saved_destroy(self, api_client):
        super().make_test(api_client)

    def case_test(self, client: APIClient, instance: User) -> Response:
        post_id = self.register_saved_post(client, instance)
        client.force_authenticate(instance)
        return client.delete(reverse_lazy(self.endpoint_detail, kwargs={"id": post_id}))

    def assert_case_test(self, response: Response, *args) -> None:
        self.assert_response(response, status.HTTP_204_NO_CONTENT)
        assert Saved.objects.count() == 0  # noqa
