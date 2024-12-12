import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer


class NotificationConsumer(AsyncWebsocketConsumer):
    user_id: int | None
    group_name: str | None

    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        if self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        if data["type"] == "authenticate":
            await self.authenticate(data["token"], data["user_id"])

    async def notify(self, event):
        await self.send(text_data=json.dumps({"payload": event["payload"]}))

    async def authenticate(self, token: str, user_id: int):
        token = await database_sync_to_async(self.check_token)(token)
        if token:
            self.group_name = f"user_{user_id}"
            self.user_id = user_id
            await self.channel_layer.group_add(self.group_name, self.channel_name)

    def check_token(self, token: str):
        from rest_framework.authtoken.models import Token

        return Token.objects.filter(key=token).exists()  # noqa
