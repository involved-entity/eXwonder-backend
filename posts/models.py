from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.validators import MinLengthValidator

User = get_user_model()


def post_images_upload(instance: 'PostImage', filename: str) -> str:
    return f"{settings.POSTS_IMAGES_DIR}/{filename}"


class PostImage(models.Model):
    image = models.ImageField(upload_to=post_images_upload)
    post = models.ForeignKey("Post", related_name="images", on_delete=models.CASCADE)


class Post(models.Model):
    author = models.ForeignKey(User, related_name="posts", on_delete=models.CASCADE)
    signature = models.CharField(max_length=512, default="")
    time_added = models.DateTimeField(auto_now_add=True)


class Like(models.Model):
    author = models.ForeignKey(User, related_name="likes", on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name="likes", on_delete=models.CASCADE)


class Comment(models.Model):
    author = models.ForeignKey(User, related_name="comments", on_delete=models.CASCADE)
    comment = models.TextField(max_length=2048, validators=(MinLengthValidator(10),))
    post = models.ForeignKey(Post, related_name="comments", on_delete=models.CASCADE)
