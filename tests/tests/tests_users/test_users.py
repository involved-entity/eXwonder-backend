import json
import random
import typing

import pytest
import pytz
from django.contrib.auth import authenticate, get_user_model
from django.urls import reverse_lazy
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from tests import GenericTest

User = get_user_model()
pytestmark = [pytest.mark.django_db]

ResponseContent = typing.Dict


class TestUsersCreation(GenericTest):
    endpoint_list = "users:account-list"
    endpoint_detail = "users:account-detail"

    def test_users_creation(self, api_client):
        super().make_test(api_client)


class TestUsersPermissions(GenericTest):
    endpoint_list = "users:account-list"
    endpoint_detail = "users:account-detail"

    def test_users_permissions(self, api_client):
        super().make_test(api_client)

    def case_test(self, client: APIClient, instance: User) -> None:
        self.send_endpoint_detail_request(client, status.HTTP_401_UNAUTHORIZED, pk=instance.pk)
        client.force_authenticate(instance)
        self.send_endpoint_detail_request(client, status.HTTP_200_OK, pk=instance.pk)


class TestUsersRetrieve(GenericTest):
    endpoint_list = "users:account-list"
    endpoint_detail = "users:account-detail"

    def test_users_retrieve(self, api_client):
        super().make_test(api_client)

    def case_test(self, client: APIClient, instance: User) -> None:
        client.force_authenticate(instance)
        user_for_check = random.choice(User.objects.filter())
        self.check_user_data(client, user_for_check)


class TestUsersUpdate(GenericTest):
    endpoint_list = "users:account-list"
    endpoint_detail = "users:account-detail"

    def test_users_update(self, api_client):
        super().make_test(api_client)

    def case_test(self, client: APIClient, instance: User) -> None:
        client.force_authenticate(instance)
        data = {
            "email": self.User.stub().email,
            "timezone": random.choice(pytz.common_timezones),
            "is_2fa_enabled": True
        }
        kwargs = {"pk": instance.pk}
        client.patch(reverse_lazy(self.endpoint_detail, kwargs=kwargs), data=data)
        self.check_user_data(client, User.objects.get(username=instance.username))


class TestUsersLogin(GenericTest):
    endpoint_list = "users:account-list"
    endpoint_detail = "users:account-detail"
    endpoint_login = "users:account-login"

    def test_users_login(self, api_client):
        super().make_test(api_client, stub=True)

    def case_test(self, client: APIClient, instance: User) -> Response:
        data = {
            "username": instance.username,
            "password": instance.password
        }
        return client.post(reverse_lazy(self.endpoint_login), data=data)

    def assert_case_test(self, response: Response, *args) -> None:
        content = json.loads(response.content)
        assert response.status_code == status.HTTP_200_OK
        assert "token" in list(content.keys())


class TestUsersPasswordChange(GenericTest):
    endpoint_list = "users:account-list"
    endpoint_detail = "users:account-detail"
    endpoint_password_change = "users:password-change"

    def test_users_password_change(self, api_client):
        super().make_test(api_client, stub=True)

    def case_test(self, client: APIClient, instance: User) -> typing.Tuple[Response, str, str]:
        client.force_authenticate(User.objects.get(username=instance.username))
        new_password = self.User.stub().password
        data = {
            "old_password": instance.password,
            "new_password1": new_password,
            "new_password2": new_password
        }
        return client.post(reverse_lazy(self.endpoint_password_change), data=data), instance.username, new_password

    def assert_case_test(self, response: Response, *args) -> None:
        assert response.status_code == status.HTTP_200_OK
        assert authenticate(username=args[0], password=args[1])
