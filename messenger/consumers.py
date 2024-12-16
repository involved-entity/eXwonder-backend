import json
import typing

from channels.db import database_sync_to_async

from common.consumers import CommonConsumer
from messenger.services import (
    create_chat,
    create_message,
    edit_message,
    get_chats,
    get_messages_in_chat,
    mark_chat,
    mark_message,
)


class MessengerConsumer(CommonConsumer):
    chats: typing.List[str]

    async def connect(self):
        await self.channel_layer.group_add(f"user_{self.user_id}", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if len(self.chats):
            _ = (await self.channel_layer.group_discard(chat, self.channel_name) for chat in self.chats)

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
            case "get_chat_history":
                await self.get_chat_history(data)
            case "start_chat":
                await self.start_chat(data)
            case "send_message":
                await self.send_message(data)
            case "read_message":
                message = await self.mark_as(data, mark_message, is_read=True)
                await self.channel_layer.group_send(
                    f"chat_{message.chat.pk}",  # noqa
                    {
                        "type": "send_read_message",
                        "message": message,
                    },
                )
            case "delete_message":
                message = await self.mark_as(data, mark_message, is_delete=True)
                await self.channel_layer.group_send(
                    f"chat_{message.chat.pk}",  # noqa
                    {
                        "type": "send_delete_message",
                        "message": message,
                    },
                )
            case "edit_message":
                message = await self.edit_message(data)
                await self.channel_layer.group_send(
                    f"chat_{message.chat.id}", {"type": "send_edit_message", "message": message}
                )
            case "delete_chat":
                chat = await self.mark_as(data, mark_chat, is_delete=True)
                await self.channel_layer.group_send(
                    f"chat_{chat.pk}",  # noqa
                    {
                        "type": "send_delete_chat",
                        "chat": chat,
                    },
                )

    async def send_read_message(self, message):
        from messenger.serializers import MessageSerializer

        await self.send(
            text_data=json.dumps({"type": "send_read_message", "message": MessageSerializer(instance=message).data})
        )

    async def send_delete_message(self, message):
        from messenger.serializers import MessageSerializer

        await self.send(
            text_data=json.dumps({"type": "send_delete_message", "message": MessageSerializer(instance=message).data})
        )

    async def send_edit_message(self, message):
        from messenger.serializers import MessageSerializer

        await self.send(
            text_data=json.dumps({"type": "send_edit_message", "message": MessageSerializer(instance=message).data})
        )

    async def send_delete_chat(self, chat):
        from messenger.serializers import ChatSerializer

        await self.send(text_data=json.dumps({"type": "send_delete_chat", "chat": ChatSerializer(instance=chat).data}))

    async def connect_to_chats(self):
        from messenger.serializers import ChatSerializer

        chats = await database_sync_to_async(get_chats)(self.user_id)

        for chat in chats:
            self.chats.append(f"chat_{chat.id}")
            await self.channel_layer.group_add(f"chat_{chat.id}", self.channel_name)

        payload = ChatSerializer(chats, many=True).data

        await self.send(text_data=json.dumps({"type": "connect_to_chats", "payload": payload}))

    async def get_chat_history(self, data: dict):
        from messenger.serializers import MessageSerializer

        chat = data["chat"]
        messages = await database_sync_to_async(get_messages_in_chat)(chat)
        payload = MessageSerializer(messages, many=True).data
        await self.send(text_data=json.dumps({"type": "get_chat_history", "chat": chat, "payload": payload}))

    async def start_chat(self, data: dict):
        receiver = data["receiver"]
        chat = await database_sync_to_async(create_chat)(receiver, self.user_id)
        self.chats.append(f"chat_{chat.id}")
        await self.channel_layer.group_add(f"chat_{chat.id}", self.channel_name)
        await self.channel_layer.group_send(f"user_{receiver}", {"type": "connect_to_chat", "chat": chat})

    async def connect_to_chat(self, event):
        from messenger.serializers import ChatSerializer

        chat = event["chat"]
        self.chats.append(f"chat_{chat.id}")
        await self.channel_layer.group_add(f"chat_{chat.id}", self.channel_name)
        payload = ChatSerializer(chat, many=True).data
        await self.send(text_data=json.dumps({"type": "connect_to_chat", "payload": payload}))

    async def send_message(self, data: dict):
        chat_id = data["chat_id"]
        receiver = data["receiver"]
        body = data.get("body", None)
        attachment = data.get("attachment", None)
        message = await database_sync_to_async(create_message)(receiver, body, attachment, self.user_id)
        await self.channel_layer.group_send(
            f"chat_{chat_id}",
            {
                "type": "on_message",
                "message": message,
            },
        )

    async def edit_message(self, data: dict):
        message = data["message"]
        body = data["body"]
        return await database_sync_to_async(edit_message)(message, body)

    async def on_message(self, event: dict):
        from messenger.serializers import MessageSerializer

        message = event["message"]
        payload = MessageSerializer(instance=message).data
        await self.send(text_data=json.dumps({"type": "on_message", "payload": payload}))

    async def mark_as(self, data: dict, callback: typing.Callable, **kwargs):
        pk = data["id"]
        await database_sync_to_async(callback)(pk, **kwargs)
