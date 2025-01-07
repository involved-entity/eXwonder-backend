from typing import NamedTuple

import pytest
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

from messenger.consumers import MessengerConsumer
from messenger.models import Chat, Message
from tests.factories import UserFactory

User = get_user_model()

DEFAULT_TIMEOUT = 30

AuthToken = str


class UserData(NamedTuple):
    user: User
    token: AuthToken


@pytest.mark.django_db
class TestMessengerConsumer:
    async def get_communicator(self, user: User) -> WebsocketCommunicator:
        communicator = WebsocketCommunicator(MessengerConsumer.as_asgi(), f"user_{user.id}_messenger")
        connected, _ = await communicator.connect(DEFAULT_TIMEOUT)
        assert connected
        return communicator

    async def get_authenticated_communicator(self, user: UserData) -> WebsocketCommunicator:
        communicator = await self.get_communicator(user.user)
        await communicator.send_json_to({"type": "authenticate", "token": user.token, "user_id": user.user.id})
        response = await communicator.receive_json_from(DEFAULT_TIMEOUT)
        assert response["authenticated"]
        return communicator

    async def test_connect(self, user1: UserData):
        await self.get_communicator(user1.user)

    async def test_disconnect(self, user1: UserData):
        communicator = await self.get_communicator(user1.user)
        await communicator.disconnect()

    async def test_authenticate(self, user1: UserData):
        await self.get_authenticated_communicator(user1)

    async def test_start_chat(self, user1: UserData, user2: UserData):
        communicator = await self.get_authenticated_communicator(user1)
        await communicator.send_json_to({"type": "start_chat", "receiver": user2.user.id})
        response = await communicator.receive_json_from(DEFAULT_TIMEOUT)
        assert response["type"] == "chat_started"

    async def test_send_message(self, user1: User, user2: User):
        chat = await database_sync_to_async(Chat.objects.create)()  # noqa
        await database_sync_to_async(chat.members.add)(user1.user, user2.user)
        communicator = await self.get_authenticated_communicator(user1)
        await communicator.send_json_to(
            {"type": "send_message", "chat_id": chat.id, "receiver": user2.user.id, "body": "Hi"}
        )
        response = await communicator.receive_json_from(DEFAULT_TIMEOUT)
        assert response["success"]

    async def test_get_chat_history(self, user1: UserData, user2: UserData):
        chat = await database_sync_to_async(Chat.objects.create)()  # noqa
        await database_sync_to_async(chat.members.add)(user1.user, user2.user)
        await database_sync_to_async(Message.objects.create)(  # noqa
            chat=chat, sender=user1.user, receiver=user2.user, body="Hi"
        )
        communicator = await self.get_authenticated_communicator(user1)
        await communicator.send_json_to({"type": "get_chat_history", "chat": chat.id})
        response = await communicator.receive_json_from(DEFAULT_TIMEOUT)
        assert response["type"] == "get_chat_history"

    async def test_delete_message(self, user1: UserData, user2: UserData):
        chat = await database_sync_to_async(Chat.objects.create)()  # noqa
        await database_sync_to_async(chat.members.add)(user1.user, user2.user)
        message = await database_sync_to_async(Message.objects.create)(  # noqa
            chat=chat, sender=user1.user, receiver=user2.user, body="Hi"
        )
        communicator = await self.get_authenticated_communicator(user1)
        await communicator.send_json_to({"type": "delete_message", "id": message.id})
        response = await communicator.receive_json_from(DEFAULT_TIMEOUT)
        assert response["success"]

    async def test_edit_message(self, user1: UserData, user2: UserData):
        chat = await database_sync_to_async(Chat.objects.create)()  # noqa
        await database_sync_to_async(chat.members.add)(user1.user, user2.user)
        message = await database_sync_to_async(Message.objects.create)(  # noqa
            chat=chat, sender=user1.user, receiver=user2.user, body="Hi"
        )
        communicator = await self.get_authenticated_communicator(user1)
        await communicator.send_json_to({"type": "edit_message", "message": message.id, "body": "World"})
        response = await communicator.receive_json_from(DEFAULT_TIMEOUT)
        assert response["success"]

    async def test_delete_chat(self, user1: UserData, user2: UserData):
        chat = await database_sync_to_async(Chat.objects.create)()  # noqa
        await database_sync_to_async(chat.members.add)(user1.user, user2.user)
        communicator = await self.get_authenticated_communicator(user1)
        await communicator.send_json_to({"type": "delete_chat", "id": chat.id})
        response = await communicator.receive_json_from(DEFAULT_TIMEOUT)
        assert response["success"]

    @pytest.fixture(autouse=True)
    async def user1(self) -> UserData:
        user = await database_sync_to_async(User.objects.create_user)(
            username=UserFactory.stub().username,
            password="testpass",
            email="",
            avatar=settings.DEFAULT_USER_AVATAR_PATH,
            timezone=settings.DEFAULT_USER_TIMEZONE,
        )
        token = await database_sync_to_async(Token.objects.create)(user=user)  # noqa
        return UserData(user, token.key)

    @pytest.fixture(autouse=True)
    async def user2(self) -> UserData:
        user = await database_sync_to_async(User.objects.create_user)(
            username=UserFactory.stub().username,
            password="testpass",
            email="",
            avatar=settings.DEFAULT_USER_AVATAR_PATH,
            timezone=settings.DEFAULT_USER_TIMEZONE,
        )
        token = await database_sync_to_async(Token.objects.create)(user=user)  # noqa
        return UserData(user, token.key)
