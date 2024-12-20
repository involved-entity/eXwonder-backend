from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

User = get_user_model()


def message_attachments_upload(instance: "Message", filename: str) -> str:
    return f"{settings.MESSAGES_ATTACHMENTS_DIR}/{filename}"


class Chat(models.Model):
    members = models.ManyToManyField(User, related_name="chats")
    is_read = models.BooleanField(default=False)
    is_delete = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("Chat")
        verbose_name_plural = _("Chats")

        db_table = "chats"

    def __str__(self) -> str:
        return f"{self.id} chat"  # noqa

    def save(self, *args, **kwargs):
        if self.id and self.members.count() > 2:  # noqa
            raise ValidationError(_("A chat can have no more than 2 members."))
        super().save(*args, **kwargs)


class Message(models.Model):
    chat = models.ForeignKey(Chat, related_name="messages", on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name="sended_messages", on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name="recieved_messages", on_delete=models.CASCADE)
    body = models.TextField(max_length=4096, null=True)
    attachment = models.FileField(upload_to=message_attachments_upload, null=True)
    time_added = models.DateTimeField(auto_now_add=True)
    time_updated = models.DateTimeField(auto_now=True)
    is_edit = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    is_delete = models.BooleanField(default=False)

    class Meta:
        ordering = ("-time_added", "-time_updated")
        verbose_name = _("Message")
        verbose_name_plural = _("Messages")

        db_table = "messages"

        constraints = [
            models.CheckConstraint(
                check=Q(body__isnull=False) | Q(attachment__isnull=False), name="body_or_attachment_required"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.sender} message to {self.receiver} at {self.time_added}"
