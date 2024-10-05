import typing

from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework.test import APIClient

from tests.mixins import RegisterObjectsMixin

User = get_user_model()

AnyParamsToAssert = typing.Any


class GenericTest(RegisterObjectsMixin):
    endpoint_list: str = None
    endpoint_detail: str = None

    tests_count: int = 2
    list_tests_count: int = 5

    def make_test(self, api_client: typing.Type[APIClient], stub: bool = False) -> None:
        client = api_client()
        users = self.get_iterable(client, stub=stub)

        for user in users:
            ret = self.case_test(client, user)

            if isinstance(ret, tuple):
                response = ret[0]
                args = ret[1:]
            elif isinstance(ret, Response):
                response = ret
                args = tuple()
            else:
                return

            self.assert_case_test(response, *args)
            self.after_assert(client, *args)

    def get_iterable(self, client: APIClient, stub: bool = False) -> typing.Iterable:
        return self.register_users(client, self.tests_count, stub=stub)

    def case_test(self, client: APIClient, instance: User) -> typing.Tuple[Response, AnyParamsToAssert] | None:
        pass

    def assert_case_test(self, response: Response, *args) -> None:
        pass

    def after_assert(self, client: APIClient, *args) -> None:
        pass
