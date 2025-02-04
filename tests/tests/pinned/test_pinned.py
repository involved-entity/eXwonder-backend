import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from posts.models import Post
from tests import GenericTest

User = get_user_model()
pytestmark = [pytest.mark.django_db]


class TestPin(GenericTest):
    endpoint_list = "posts:pinned-pin"

    def test_pin(self, api_client):
        super().make_test(api_client)

    def case_test(self, client: APIClient, instance: User) -> Response:
        posts = [self.register_pinned_post(client, instance) for _ in range(3)]
        user = self.register_users(client, 1)[0]

        client.force_authenticate(user)
        response = client.post(reverse_lazy(self.endpoint_list, kwargs={"pk": posts[0].pk}))
        assert response.status_code == status.HTTP_403_FORBIDDEN

        post = self.register_post(client, instance)
        client.force_authenticate(instance)
        return client.post(reverse_lazy(self.endpoint_list, kwargs={"pk": post.pk}))

    def assert_case_test(self, response: Response, *args) -> None:
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestUnpin(GenericTest):
    endpoint_list = "posts:pinned-unpin"

    def test_unpin(self, api_client):
        super().make_test(api_client)

    def case_test(self, client: APIClient, instance: User) -> None:
        posts = [self.register_pinned_post(client, instance) for _ in range(3)]
        assert Post.objects.filter(author=instance, pinned=True).count() == 3
        client.force_authenticate(instance)
        for i in range(3):
            response = client.post(reverse_lazy(self.endpoint_list, kwargs={"pk": posts[i].pk}))
            assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Post.objects.filter(author=instance, pinned=True).count() == 0
