import typing

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from tests.factories import PostFactory, UserFactory

User = get_user_model()


@pytest.fixture(scope="session")
def user_factory() -> typing.Type[UserFactory]:
    return UserFactory


@pytest.fixture(scope="session")
def api_client() -> typing.Type[APIClient]:
    return APIClient


@pytest.fixture(scope="session")
def post_factory() -> typing.Type[PostFactory]:
    return PostFactory
