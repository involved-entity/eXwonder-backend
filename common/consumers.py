import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer


class CommonConsumer(AsyncWebsocketConsumer):
    user_id: int | None
    group_name: str | None

    async def authenticate(self, token: str, user_id: int):
        token = await database_sync_to_async(self.check_token)(token)
        if token:
            await self.create_group(user_id)
            await self.send(text_data=json.dumps({"authenticated": True}))
        else:
            await self.send(text_data=json.dumps({"authenticated": False}))

    def check_token(self, token: str):
        from rest_framework.authtoken.models import Token

        return Token.objects.filter(key=token).exists()  # noqa

    async def create_group(self, user_id: int):
        raise NotImplementedError()
