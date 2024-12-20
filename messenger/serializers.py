import urllib.parse

from django.conf import settings
from rest_framework import serializers

from common.services import datetime_to_timezone
from messenger.models import Chat, Message
from users.serializers import UserDefaultSerializer


class FileField(serializers.FileField):
    def to_representation(self, value):
        if not value:
            return None
        media_url = urllib.parse.urljoin(settings.HOST, settings.MEDIA_URL)
        return {"link": urllib.parse.urljoin(media_url, str(value)), "name": str(value)}


class MessageSerializer(serializers.ModelSerializer):
    sender = UserDefaultSerializer()
    receiver = UserDefaultSerializer()
    time_added = serializers.SerializerMethodField()
    time_updated = serializers.SerializerMethodField()
    attachment = FileField()

    class Meta:
        model = Message
        fields = (
            "id",
            "chat",
            "sender",
            "receiver",
            "body",
            "attachment",
            "time_added",
            "time_updated",
            "is_edit",
            "is_read",
        )

    def get_time_added(self, instance: Message) -> dict:
        return datetime_to_timezone(instance.time_added, self.context["user"].timezone, to_timesince=False)

    def get_time_updated(self, instance: Message) -> dict:
        return datetime_to_timezone(
            instance.time_updated, self.context["user"].timezone, attribute_name="time_updated", to_timesince=False
        )


class ChatSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = "id", "user", "last_message", "is_read"

    def get_user(self, instance: Chat) -> dict:
        user = instance.members.exclude(id=self.context["user"].id)[0]
        return UserDefaultSerializer(instance=user).data

    def get_last_message(self, instance: Chat) -> dict:
        message = instance.messages.filter(is_delete=False).order_by("-time_added").first()  # noqa
        return MessageSerializer(instance=message, context=self.context).data
