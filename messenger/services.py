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


def get_new_chat_entity(message_pk: int):
    from messenger.models import Message

    return Message.objects.select_related("chat").prefetch_related("chat__members").get(pk=message_pk).chat


def get_chats(user: "User") -> QuerySet:
    return list(user.chats.prefetch_related("members", "messages").filter(is_delete=False))


def get_chat(pk: int):
    from messenger.models import Chat

    return Chat.objects.prefetch_related("members", "messages").get(pk=pk)


def get_messages_in_chat(chat: int):
    from messenger.models import Chat

    return list(Chat.objects.get(pk=chat).messages.select_related("sender", "receiver").filter(is_delete=False))  # noqa


def create_chat(receiver: int, user: "User"):
    from messenger.models import Chat

    User = get_user_model()  # noqa
    removed_chat = Chat.objects.filter(Q(members__id=receiver) & Q(members__id=user.id))  # noqa

    if removed_chat.exists():
        chat = removed_chat[0]
        chat.is_delete = False
        chat.save()
        return chat

    chat = Chat.objects.create()  # noqa
    members = User.objects.filter(pk__in={receiver, user.id})
    chat.members.add(*list(members))
    return chat


def create_message(
    chat: int, receiver: int, body: str | None, attachment: typing.Any, attachment_name: str | None, user: "User"
):
    from messenger.models import Chat, Message

    file = ContentFile(attachment, name=attachment_name) if attachment else None

    chat = Chat.objects.get(pk=chat)
    chat.is_read = False
    chat.save()
    return Message.objects.create(  # noqa
        chat=chat, sender=user, receiver_id=receiver, body=body, attachment=file
    )


def mark_message(pk: int, user: "User", **kwargs):
    from messenger.models import Message

    message = Message.objects.select_related("chat").prefetch_related("chat__messages").get(pk=pk)  # noqa
    for key, value in kwargs.items():
        setattr(message, key, value)
    message.save()
    if "is_delete" in kwargs:
        new_last_message = message.chat.messages.filter(is_delete=False).order_by("-time_added").first()
        message.chat.is_read = new_last_message.is_read
        message.chat.save()
    return message


def mark_chat(pk: int, user: "User", **kwargs):
    from messenger.models import Chat

    chat = Chat.objects.get(pk=pk)  # noqa
    chat.messages.update(**kwargs)
    for key, value in kwargs.items():
        setattr(chat, key, value)
    chat.save()
    return chat


def edit_message(message: int, body: str, attachment: typing.Any, attachment_name: str | None):
    from messenger.models import Message

    message = Message.objects.select_related("chat").get(pk=message)  # noqa
    message.body = body
    if attachment and attachment_name:
        file = ContentFile(attachment, name=attachment_name)
        message.attachment = file
    message.is_edit = True
    message.save()
    return message
