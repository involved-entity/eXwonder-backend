from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from posts.models import Post

User = get_user_model()


class Notification(models.Model):
    recipient = models.ForeignKey(User, related_name="notifications", on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name="notifications", on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    time_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-time_added",)
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")

    def __str__(self):
        return f"{self.recipient} notification about {self.post} post (read={self.is_read})"
