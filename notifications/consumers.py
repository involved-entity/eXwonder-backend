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
        type_ = data.get("type")

        match type_:
            case "authenticate":
                await self.authenticate(data.get("token"), data.get("user_id"))
            case "get_unreaded_notifications":
                await self.return_unreaded_notifications()
            case "mark_read":
                await database_sync_to_async(self.mark_read)(data.get("id"))
            case "mark_all_read":
                await database_sync_to_async(self.mark_all_read)()

    async def return_unreaded_notifications(self):
        payload = []
        notifications = await database_sync_to_async(self.get_unreaded_notifications)()
        if len(notifications):
            from notifications.serializers import NotificationSerializer

            payload = NotificationSerializer(notifications, many=True).data

        await self.send(text_data=json.dumps({"type": "get_unreaded_notifications", "payload": payload}))

    def mark_read(self, pk: int):
        if pk:
            from notifications.models import Notification

            Notification.objects.select_related("recipient").filter(recipient__id=self.user_id, pk=pk).update(
                is_read=True
            )

    def mark_all_read(self):
        from notifications.models import Notification

        Notification.objects.select_related("recipient").filter(recipient__id=self.user_id, is_read=False).update(
            is_read=True
        )

    def get_unreaded_notifications(self):
        from notifications.models import Notification

        return list(
            Notification.objects.select_related("recipient", "post__author").filter(
                recipient__id=self.user_id, is_read=False
            )
        )

    async def notify(self, event):
        await self.send(text_data=json.dumps({"type": "notify", "payload": event["payload"]}))

    async def authenticate(self, token: str, user_id: int):
        token = await database_sync_to_async(self.check_token)(token)
        if token:
            self.group_name = f"user_{user_id}"
            self.user_id = user_id
            await self.channel_layer.group_add(self.group_name, self.channel_name)

    def check_token(self, token: str):
        from rest_framework.authtoken.models import Token

        return Token.objects.filter(key=token).exists()  # noqa
