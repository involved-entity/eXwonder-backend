import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from posts.models import PostLike
from tests import GenericTest

User = get_user_model()
pytestmark = [pytest.mark.django_db]


class TestLikesCreation(GenericTest):
    endpoint_list = "posts:likes-list"
    endpoint_detail = "posts:likes-detail"

    def test_likes_creation(self, api_client):
        super().make_test(api_client)

    def case_test(self, client: APIClient, instance: User) -> None:
        self.register_like(client, instance)


class TestLikesDelete(GenericTest):
    endpoint_list = "posts:likes-list"
    endpoint_detail = "posts:likes-detail"

    def test_likes_delete(self, api_client):
        super().make_test(api_client)

    def case_test(self, client: APIClient, instance: User) -> Response:
        user, post_id = self.register_like(client, instance)
        client.force_authenticate(instance)
        return client.delete(reverse_lazy(self.endpoint_detail, kwargs={"post_id": post_id}))

    def assert_case_test(self, response: Response, *args) -> None:
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert PostLike.objects.filter().count() == 0  # noqa
