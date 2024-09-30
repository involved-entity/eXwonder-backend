import json
import typing
import random

import pytest
import pytz
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from rest_framework import status
from rest_framework.test import APIClient

from tests.factories import UserFactory

User = get_user_model()
pytestmark = [pytest.mark.django_db]

BatchCreatedUsers = typing.List
ResponseContent = typing.Dict


class TestUsers(object):
    endponint_list = reverse_lazy("api:account-list")
    endponint_detail = "api:account-detail"
    tests_count = 2

    def __send_endpoint_detail_request(self, client: APIClient, pk: int, status__: int) -> ResponseContent:
        detail_url = reverse_lazy(self.endponint_detail, kwargs={"pk": pk})
        response = client.get(detail_url)
        assert response.status_code == status__
        return json.loads(response.content)

    def __get_users_for_test(self, user_factory: typing.Type[UserFactory]) -> BatchCreatedUsers:
        return user_factory.create_batch(self.tests_count)

    def __check_user_data(self, client: APIClient, valid_user: User) -> None:
        content = self.__send_endpoint_detail_request(client, valid_user.pk, status.HTTP_200_OK)
        assert content["id"] == valid_user.pk
        assert content["username"] == valid_user.username
        assert content["email"] == valid_user.email
        assert content["timezone"] == valid_user.timezone
        assert content["is_2fa_enabled"] == valid_user.is_2fa_enabled

    def test_user_creation(self, api_client: typing.Type[APIClient], user_factory: typing.Type[UserFactory]) -> None:
        client = api_client()
        users_data = user_factory.stub_batch(self.tests_count)
        for user_data in users_data:
            data = {
                "username": user_data.username,
                "email": user_data.email,
                "password": user_data.password,
            }
            response = client.post(self.endponint_list, data=data)
            assert response.status_code == status.HTTP_201_CREATED

    def test_user_permissions(self, api_client: typing.Type[APIClient], user_factory: typing.Type[UserFactory]) -> None:
        client = api_client()
        users = self.__get_users_for_test(user_factory)
        for user in users:
            self.__send_endpoint_detail_request(client, user.pk, status.HTTP_403_FORBIDDEN)

    def test_user_retrive(self, api_client: typing.Type[APIClient], user_factory: typing.Type[UserFactory]) -> None:
        client = api_client()
        users = self.__get_users_for_test(user_factory)
        for user in users:
            client.force_authenticate(user)
            user_for_check = random.choice(users)
            self.__check_user_data(client, user_for_check)

    def test_user_update(self, api_client: typing.Type[APIClient], user_factory: typing.Type[UserFactory]) -> None:
        client = api_client()
        users = self.__get_users_for_test(user_factory)
        for user in users:
            client.force_authenticate(user)
            data = {
                "email": user_factory.stub().email,
                "timezone": random.choice(pytz.common_timezones),
                "is_2fa_enabled": True
            }
            response = client.patch(reverse_lazy(self.endponint_detail, kwargs={"pk": user.pk}), data=data)
            assert response.status_code == status.HTTP_200_OK
            self.__check_user_data(client, User.objects.get(pk=user.pk))
