from django.contrib.auth import get_user_model
from django.db import models

from posts.models import Post

User = get_user_model()


class Notification(models.Model):
    recipient = models.ForeignKey(User, related_name="notifications", on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name="notifications", on_delete=models.CASCADE)
    time_added = models.DateTimeField(auto_now_add=True)
