import random
import typing

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from rest_framework import status
from rest_framework.test import APIClient

from tests import FollowTestMode, FollowTestService, register_users
from tests.factories import UserFactory

User = get_user_model()
pytestmark = [pytest.mark.django_db]

UserFollower = UserFollowing = User
UsersWithFollowsRelations = typing.List[typing.Tuple[UserFollower, UserFollowing]]


class TestFollowings(object):
    endpoint_list = "users:followings-list"
    endpoint_disfollow = "users:followings-disfollow"
    endpoint_user = "users:followings-user"

    tests_count = 2
    list_tests_count = 5

    def __get_registered_user_objects(self, client: APIClient, user_factory: typing.Type[UserFactory]) \
            -> typing.List[User]:
        users = register_users(client, user_factory, self.tests_count)
        return list(map(lambda u: User.objects.get(username=u.username), users))

    def __get_users_with_follows_relations(self, client: APIClient, user_factory: typing.Type[UserFactory]) \
            -> UsersWithFollowsRelations:
        relations = []
        url = reverse_lazy(self.endpoint_list)
        users = self.__get_registered_user_objects(client, user_factory)

        for user in users:
            client.force_authenticate(user)
            copy = users.copy()
            copy.remove(user)
            following = random.choice(copy)
            response = client.post(url, data={"following": following.pk})
            assert response.status_code == status.HTTP_201_CREATED
            assert user.following.count() == 1
            relations.append((user, following))

        return relations   # noqa

    def test_followings_creation(self, api_client: typing.Type[APIClient], user_factory: typing.Type[UserFactory]) \
            -> None:
        client = api_client()
        self.__get_users_with_follows_relations(client, user_factory)

    def test_followings_disfollow(self, api_client: typing.Type[APIClient], user_factory: typing.Type[UserFactory]) \
            -> None:
        client = api_client()
        relations = self.__get_users_with_follows_relations(client, user_factory)
        url = reverse_lazy(self.endpoint_disfollow)

        for relation in relations:
            client.force_authenticate(relation[0])
            response = client.delete(url, data={"following": relation[1].pk})
            assert response.status_code == status.HTTP_204_NO_CONTENT

        for follower in [relation[0] for relation in relations]:
            assert follower.followers.count() == 0 and follower.following.count() == 0

    def test_followings_of_user(self, api_client: typing.Type[APIClient], user_factory: typing.Type[UserFactory]) \
            -> None:
        client = api_client()
        service = FollowTestService(
            self.endpoint_list,
            self.endpoint_list,
            self.list_tests_count,
            FollowTestMode.FOLLOWINGS
        )
        for _ in range(self.tests_count):
            service.make_follow_test(client, user_factory)

    def test_followings_of_each_user(self, api_client: typing.Type[APIClient], user_factory: typing.Type[UserFactory]) \
            -> None:
        client = api_client()
        service = FollowTestService(
            self.endpoint_list,
            self.endpoint_user,
            self.list_tests_count,
            FollowTestMode.FOLLOWINGS_EACH_USER
        )
        for _ in range(self.tests_count):
            service.make_follow_test(client, user_factory)
