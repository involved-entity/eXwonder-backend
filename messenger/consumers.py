import json

from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

from common.consumers import CommonConsumer

User = get_user_model()


class MessengerConsumer(CommonConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        if self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def create_group(self, user_id: int):
        self.user_id = user_id

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        type_ = data.get("type")

        match type_:
            case "authenticate":
                await self.authenticate(data.get("token"), data.get("user_id"))
            case "connect_to_chats":
                await self.connect_to_chats()

    async def connect_to_chats(self):
        from messenger.serializers import ChatSerializer

        chats = await database_sync_to_async(self.get_chats)()
        for chat in chats:
            await self.channel_layer.group_add(f"chat_{chat.id}", self.channel_name)
        payload = ChatSerializer(chats, many=True).data

        await self.send(text_data=json.dumps({"type": "connect_to_chats", "payload": payload}))

    def get_chats(self):
        return User.objects.get(pk=self.user_id).chats.prefetch_related("members", "messages")
