import typing

from django.contrib.auth import get_user_model
from django.db.models import QuerySet


def get_chats(user_id: int) -> QuerySet:
    User = get_user_model()  # noqa
    return list(User.objects.get(pk=user_id).chats.prefetch_related("members", "messages").filter(is_delete=False))


def get_messages_in_chat(chat: int):
    from messenger.models import Chat

    return list(Chat.objects.get(pk=chat).messages.filter())  # noqa


def create_chat(receiver: int, user_id: int):
    from messenger.models import Chat

    User = get_user_model()  # noqa
    members = User.objects.filter(id__in={receiver, user_id})
    removed_chat = Chat.objects.filter(members=members)  # noqa

    if removed_chat:
        chat = removed_chat[0]
        chat.is_delete = False
        chat.save()
        return chat

    chat = Chat.objects.create()  # noqa
    chat.members.add(*list(members))
    return chat


def create_message(receiver: int, body: str | None, attachment: typing.Any, user_id: int):
    from messenger.models import Message

    return Message.objects.create(  # noqa
        sender_id=user_id, receiver_id=receiver, body=body, attachment=attachment
    )


def mark_message(pk: int, **kwargs):
    from messenger.models import Message
    from messenger.serializers import MessageSerializer

    message = Message.objects.select_related("chat").filter(pk=pk)  # noqa
    message.update(**kwargs)
    return MessageSerializer(instance=message).data


def mark_chat(pk: int, **kwargs):
    from messenger.models import Chat
    from messenger.serializers import ChatSerializer

    chat = Chat.objects.filter(pk=pk)  # noqa
    if "is_delete" in kwargs:
        chat.messages.update(**kwargs)
    chat.update(**kwargs)
    return ChatSerializer(instance=chat).data


def edit_message(message: int, body: str):
    from messenger.models import Message

    message = Message.objects.select_related("chat").get(pk=message)  # noqa
    message.body = body
    message.save()
    return message
