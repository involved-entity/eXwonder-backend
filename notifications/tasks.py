from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model

from notifications.models import Notification
from notifications.serializers import NotificationSerializer
from posts.models import Post

User = get_user_model()


@shared_task
def send_notifications(post_id: int) -> None:
    channel_layer = get_channel_layer()
    post = Post.objects.get(pk=post_id)  # noqa
    followers = [follow.follower for follow in post.author.followers.select_related("follower").all()]
    notifications = []

    for follower in followers:
        notification = Notification(recipient=follower, post=post)
        notifications.append(notification)

    Notification.objects.bulk_create(notifications)  # noqa

    for notification in notifications:
        async_to_sync(channel_layer.group_send)(
            f"user_{notification.recipient.id}_notifications",
            {  # noqa
                "type": "notify",
                "payload": NotificationSerializer(instance=notification).data,
            },
        )
