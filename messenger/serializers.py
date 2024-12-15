from rest_framework import serializers

from common.services import datetime_to_timezone
from messenger.models import Chat, Message
from users.serializers import UserDefaultSerializer


class ChatSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = "id", "user", "last_message"

    def get_user(self, instance: Chat) -> dict:
        return UserDefaultSerializer(instance=instance.members.exclude(id=self.context["request"].user.id)[0]).data

    def get_last_message(self, instance: Chat) -> str | None:
        return instance.messages.order_by("-time_added").first().body  # noqa


class MessageSerializer(serializers.ModelSerializer):
    sender = UserDefaultSerializer()
    receiver = UserDefaultSerializer()
    time_added = serializers.SerializerMethodField()
    time_updated = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = "id", "sender", "receiver", "body", "attachment", "time_added", "time_updated", "is_read"

    def get_time_added(self, instance: Message) -> dict:
        return datetime_to_timezone(instance.time_added, self.context["request"].user.timezone)

    def get_time_updated(self, instance: Message) -> dict:
        return datetime_to_timezone(instance.time_updated, self.context["request"].user.timezone)
