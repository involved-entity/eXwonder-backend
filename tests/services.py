import typing

from django.urls import reverse_lazy
from rest_framework import status
from rest_framework.test import APIClient

from tests.factories import UserFactory

BatchCreateUsers = typing.List
BatchStubUsers = typing.List

REGISTER_USERS_ENDPOINT = "api:account-list"


def get_users_for_test(user_factory: typing.Type[UserFactory], users_count: int, stub: bool = False) \
        -> BatchCreateUsers | BatchStubUsers:
    return user_factory.create_batch(users_count) if not stub else user_factory.stub_batch(users_count)


def register_users(client: APIClient, user_factory: typing.Type[UserFactory], users_count: int) -> BatchStubUsers:
    users_data = get_users_for_test(user_factory, users_count, stub=True)
    for user_data in users_data:
        data = {
            "username": user_data.username,
            "email": user_data.email,
            "password": user_data.password,
        }
        response = client.post(reverse_lazy(REGISTER_USERS_ENDPOINT), data=data)
        assert response.status_code == status.HTTP_201_CREATED
    return users_data
