from rest_framework import serializers

from notifications.models import Notification
from posts.services.services import datetime_to_timezone
from users.serializers import UserDefaultSerializer


class NotificationSerializer(serializers.ModelSerializer):
    receiver = serializers.SerializerMethodField()
    time_added = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = "id", "receiver", "is_read", "time_added"
        read_only_fields = "receiver", "is_read", "time_added"

    def get_receiver(self, instance: Notification) -> dict:
        return UserDefaultSerializer(instance=instance.post.author).data

    def get_time_added(self, instance: Notification) -> dict:
        return datetime_to_timezone(instance.time_added, instance.recipient.timezone)
