import json
import random
import typing

import pytest
import pytz
from django.contrib.auth import authenticate, get_user_model
from django.urls import reverse_lazy
from rest_framework import status
from rest_framework.test import APIClient

from tests import get_users_for_test, register_users
from tests.factories import UserFactory

User = get_user_model()
pytestmark = [pytest.mark.django_db]

ResponseContent = typing.Dict


class TestUsers(object):
    endpoint_list = "users:account-list"
    endpoint_detail = "users:account-detail"
    endpoint_login = "users:account-login"
    endpoint_password_change = "users:password-change"

    tests_count = 2

    def __send_endpoint_detail_request(self, client: APIClient, pk: int, status__: int) -> ResponseContent:
        detail_url = reverse_lazy(self.endpoint_detail, kwargs={"pk": pk})
        response = client.get(detail_url)
        assert response.status_code == status__
        return json.loads(response.content)

    def __check_user_data(self, client: APIClient, valid_user: User) -> None:
        content = self.__send_endpoint_detail_request(client, valid_user.pk, status.HTTP_200_OK)
        assert content["id"] == valid_user.pk
        assert content["username"] == valid_user.username
        assert content["email"] == valid_user.email
        assert content["timezone"] == valid_user.timezone
        assert content["is_2fa_enabled"] == valid_user.is_2fa_enabled

    def test_user_creation(self, api_client: typing.Type[APIClient], user_factory: typing.Type[UserFactory]) -> None:
        client = api_client()
        register_users(client, user_factory, self.tests_count)

    def test_user_permissions(self, api_client: typing.Type[APIClient], user_factory: typing.Type[UserFactory]) -> None:
        client = api_client()
        users = get_users_for_test(user_factory, self.tests_count)
        for user in users:
            self.__send_endpoint_detail_request(client, user.pk, status.HTTP_403_FORBIDDEN)

    def test_user_retrive(self, api_client: typing.Type[APIClient], user_factory: typing.Type[UserFactory]) -> None:
        client = api_client()
        users = get_users_for_test(user_factory, self.tests_count)
        for user in users:
            client.force_authenticate(user)
            user_for_check = random.choice(users)
            self.__check_user_data(client, user_for_check)

    def test_user_update(self, api_client: typing.Type[APIClient], user_factory: typing.Type[UserFactory]) -> None:
        client = api_client()
        users = get_users_for_test(user_factory, self.tests_count)
        for user in users:
            client.force_authenticate(user)
            data = {
                "email": user_factory.stub().email,
                "timezone": random.choice(pytz.common_timezones),
                "is_2fa_enabled": True
            }
            response = client.patch(reverse_lazy(self.endpoint_detail, kwargs={"pk": user.pk}), data=data)
            assert response.status_code == status.HTTP_200_OK
            self.__check_user_data(client, User.objects.get(pk=user.pk))

    def test_user_login(self, api_client: typing.Type[APIClient], user_factory: typing.Type[UserFactory]) -> None:
        client = api_client()
        users = register_users(client, user_factory, self.tests_count)
        for user in users:
            data = {
                "username": user.username,
                "password": user.password
            }
            response = client.post(reverse_lazy(self.endpoint_login), data=data)
            assert response.status_code == status.HTTP_200_OK
            assert "token" in list(json.loads(response.content).keys())

    def test_user_password_change(self, api_client: typing.Type[APIClient], user_factory: typing.Type[UserFactory]) \
            -> None:
        client = api_client()
        users = register_users(client, user_factory, self.tests_count)
        new_users = get_users_for_test(user_factory, self.tests_count, stub=True)
        for user, new_user in zip(users, new_users):
            client.force_authenticate(User.objects.get(username=user.username))
            data = {
                "old_password": user.password,
                "new_password1": new_user.password,
                "new_password2": new_user.password
            }
            response = client.post(reverse_lazy(self.endpoint_password_change), data=data)
            assert response.status_code == status.HTTP_200_OK
            assert authenticate(username=user.username, password=new_user.password)
