import typing

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db.models import Q, QuerySet


def get_current_user(user_id: int):
    User = get_user_model()
    return User.objects.get(pk=user_id)


def get_message(pk: int):
    from messenger.models import Message

    return Message.objects.select_related("chat", "sender", "receiver").get(pk=pk)


def get_chats(user: "User") -> QuerySet:
    return list(user.chats.prefetch_related("members", "messages").filter(is_delete=False))


def get_messages_in_chat(chat: int):
    from messenger.models import Chat

    return list(Chat.objects.get(pk=chat).messages.select_related("sender", "receiver").filter())  # noqa


def create_chat(receiver: int, user: "User"):
    from messenger.models import Chat

    User = get_user_model()  # noqa
    removed_chat = Chat.objects.filter(Q(members__id=receiver) & Q(members__id=user.id))  # noqa

    if removed_chat:
        chat = removed_chat[0]
        chat.is_delete = False
        chat.save()
        return chat

    chat = Chat.objects.create()  # noqa
    members = User.objects.filter(pk__in={receiver, user.id})
    chat.members.add(*list(members))
    return chat


def create_message(
    chat: int, receiver: int, body: str | None, attachment: typing.Any, attachment_name: str, user: "User"
):
    from messenger.models import Message

    file = ContentFile(attachment, name=attachment_name) if attachment else None

    return Message.objects.create(  # noqa
        chat_id=chat, sender=user, receiver_id=receiver, body=body, attachment=file
    )


def mark_message(pk: int, user: "User", **kwargs):
    from messenger.models import Message
    from messenger.serializers import MessageSerializer

    message = Message.objects.filter(pk=pk)  # noqa
    message.update(**kwargs)
    return MessageSerializer(instance=message, context={"user": user}).data


def mark_chat(pk: int, user: "User", **kwargs):
    from messenger.models import Chat
    from messenger.serializers import ChatSerializer

    chat = Chat.objects.filter(pk=pk)  # noqa
    if "is_delete" in kwargs:
        chat.messages.update(**kwargs)
    chat.update(**kwargs)
    return ChatSerializer(instance=chat, context={"user": user}).data


def edit_message(message: int, body: str):
    from messenger.models import Message

    message = Message.objects.get(pk=message)  # noqa
    message.body = body
    message.save()
    return message
