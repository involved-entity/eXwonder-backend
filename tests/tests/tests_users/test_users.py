import json
import random
import secrets
import string
import typing

import pytest
import pytz
from django.contrib.auth import authenticate, get_user_model
from django.urls import reverse_lazy
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from tests import AssertPaginatedResponseMixin, AssertResponseMixin, GenericTest

User = get_user_model()
pytestmark = [pytest.mark.django_db]

ResponseContent = typing.Dict


class TestUsersCreation(GenericTest):
    endpoint_list = "users:account-list"
    endpoint_detail = "users:account-detail"

    def test_users_creation(self, api_client):
        super().make_test(api_client)


class TestUsersMy(AssertResponseMixin, GenericTest):
    endpoint_detail = "users:account-my"

    def test_users_my(self, api_client):
        super().make_test(api_client)

    def case_test(self, client: APIClient, instance: User) -> typing.Tuple[Response, User]:
        client.force_authenticate(instance)
        return self.send_endpoint_detail_request(client, status.HTTP_200_OK), instance

    def assert_case_test(self, response: Response, *args) -> None:
        self.assert_response(response, needed_keys=('id', 'username', 'timezone', 'is_2fa_enabled'))


class TestUsersSearch(AssertPaginatedResponseMixin, GenericTest):
    endpoint_list = 'users:account-list'

    def test_users_search(self, api_client):
        super().make_test(api_client)

    def __generate_random_search_users(self, users_count: int) -> typing.Tuple[typing.Any, ...]:
        return tuple(self.User.stub(username="searchuser" + ''.join(secrets.choice(string.ascii_letters) for i in range(5)))
                     for i in range(users_count))

    def case_test(self, client: APIClient, instance: User) -> Response:
        users = self.User.stub_batch(self.list_tests_count - 2)
        users.extend(self.__generate_random_search_users(2))
        self.register_users(client, self.list_tests_count, users=users)
        client.force_authenticate(instance)
        return client.get(f'{reverse_lazy(self.endpoint_list)}?search=sea')

    def assert_case_test(self, response: Response, *args) -> None:
        self.assert_paginated_response(response, 2)

    def after_assert(self, client: APIClient, *args) -> None:
        User.objects.filter(username__startswith="sea").delete()


class TestUsersPermissions(GenericTest):
    endpoint_list = "users:account-list"
    endpoint_detail = "users:account-detail"

    def test_users_permissions(self, api_client):
        super().make_test(api_client)

    def case_test(self, client: APIClient, instance: User) -> None:
        self.send_endpoint_detail_request(client, status.HTTP_403_FORBIDDEN, pk=instance.pk)
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
