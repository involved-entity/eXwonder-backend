import typing

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db.models import Q


def get_current_user(user_id: int, set_online: bool = False) -> "User":
    User = get_user_model()
    user = User.objects.get(pk=user_id)
    if set_online:
        user.is_online = True
        user.save()
    return user


def set_user_offline(user: "User") -> "User":
    User = get_user_model()
    user = User.objects.get(pk=user.id)
    user.is_online = False
    user.save()
    return user


def get_message(pk: int) -> "Message":
    from messenger.models import Message

    return Message.objects.select_related("chat", "sender", "receiver").get(pk=pk)  # noqa


def get_new_chat_entity(message_pk: int) -> "Chat":
    from messenger.models import Message

    return Message.objects.select_related("chat").prefetch_related("chat__members").get(pk=message_pk).chat  # noqa


def get_chats(user: "User") -> list["Chat"]:
    return list(user.chats.prefetch_related("members", "messages").filter(is_delete=False))


def get_chat(pk: int) -> "Chat":
    from messenger.models import Chat

    return Chat.objects.prefetch_related("members", "messages").get(pk=pk)  # noqa


def get_messages_in_chat(chat: int) -> list["Messages"]:
    from messenger.models import Chat

    return list(Chat.objects.get(pk=chat).messages.select_related("sender", "receiver").filter(is_delete=False))  # noqa


def create_chat(receiver: int | str, user: "User") -> tuple["Chat", "User"]:
    from messenger.models import Chat

    User = get_user_model()  # noqa
    second_member = User.objects.filter(**{"pk" if isinstance(receiver, int) else "username": receiver})

    if not len(second_member):
        return None, None

    second_member = second_member[0]

    removed_chat = Chat.objects.filter(Q(members__id=second_member.id) & Q(members__id=user.id))  # noqa

    if removed_chat.exists():
        chat = removed_chat[0]
        chat.is_delete = False
        chat.save()
        return chat

    chat = Chat.objects.create()  # noqa
    members = User.objects.filter(pk__in={second_member.id, user.id})
    chat.members.add(*list(members))
    return chat, second_member


def create_message(
    chat: int, receiver: int, body: str | None, attachment: typing.Any, attachment_name: str | None, user: "User"
) -> "Message":
    from messenger.models import Chat, Message

    file = ContentFile(attachment, name=attachment_name) if attachment else None

    chat = Chat.objects.get(pk=chat)
    chat.is_read = False
    chat.save()
    return Message.objects.create(  # noqa
        chat=chat, sender=user, receiver_id=receiver, body=body, attachment=file
    )


def mark_message(pk: int, **kwargs) -> "Message":
    from messenger.models import Message

    message = Message.objects.select_related("chat").prefetch_related("chat__messages").get(pk=pk)  # noqa
    for key, value in kwargs.items():
        setattr(message, key, value)
    message.save()
    if "is_delete" in kwargs:
        new_last_message = message.chat.messages.filter(is_delete=False).order_by("-time_added").first()
        message.chat.is_read = new_last_message.is_read if new_last_message else True
        message.chat.save()

    return message


def mark_chat(pk: int, **kwargs) -> "Chat":
    from messenger.models import Chat

    chat = Chat.objects.get(pk=pk)  # noqa
    chat.messages.update(**kwargs)
    for key, value in kwargs.items():
        setattr(chat, key, value)
    chat.save()
    return chat


def edit_message(message: int, body: str, attachment: typing.Any, attachment_name: str | None) -> "Message":
    from messenger.models import Message

    message = Message.objects.select_related("chat").get(pk=message)  # noqa
    message.body = body
    if attachment and attachment_name:
        file = ContentFile(attachment, name=attachment_name)
        message.attachment = file
    message.is_edit = True
    message.save()
    return message
