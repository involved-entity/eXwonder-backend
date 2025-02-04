from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

User = get_user_model()


def post_images_upload(instance: "PostImage", filename: str) -> str:
    return f"{settings.POSTS_IMAGES_DIR}/{filename}"


class PostImage(models.Model):
    image = models.ImageField(upload_to=post_images_upload)
    post = models.ForeignKey("Post", related_name="images", on_delete=models.CASCADE)

    class Meta:
        verbose_name = _("Post image")
        verbose_name_plural = _("Posts images")

    def __str__(self):
        return f"Image for {self.post.pk}."  # noqa


@receiver(pre_delete, sender=PostImage)
def mymodel_delete(sender, instance, **kwargs):
    instance.image.delete(False)


class Post(models.Model):
    author = models.ForeignKey(User, related_name="posts", on_delete=models.CASCADE)
    signature = models.CharField(max_length=512, default="")
    tags = models.ManyToManyField("Tag", related_name="posts", blank=True)
    pinned = models.BooleanField(default=False)
    time_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-id",)
        verbose_name = _("Post")
        verbose_name_plural = _("Posts")

        db_table = "posts"

    def __str__(self):
        return f"{self.pk} post."

    def clean(self):
        if self.pinned:
            pinned_count = Post.objects.filter(author=self.author, pinned=True).count()
            if pinned_count >= 3:
                raise serializers.ValidationError({"pinned": "One author must have no more than 3 pinned posts."})


class Tag(models.Model):
    name = models.CharField(max_length=32, unique=True)

    class Meta:
        ordering = ("-id",)
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")

        db_table = "tags"

    def __str__(self):
        return self.name


class PostLike(models.Model):
    author = models.ForeignKey(User, related_name="likes", on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name="likes", on_delete=models.CASCADE)

    class Meta:
        verbose_name = _("Post like")
        verbose_name_plural = _("Posts likes")

    def __str__(self):
        return f"{self.author.pk} like for {self.post.pk} post."  # noqa


class Comment(models.Model):
    author = models.ForeignKey(User, related_name="comments", on_delete=models.CASCADE)
    comment = models.TextField(max_length=2048, validators=(MinLengthValidator(10),))
    post = models.ForeignKey(Post, related_name="comments", on_delete=models.CASCADE)
    time_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-time_added",)
        verbose_name = _("Comment")
        verbose_name_plural = _("Comments")

    def __str__(self):
        return f"{self.author.pk} comment for {self.post.pk}."  # noqa


class CommentLike(models.Model):
    author = models.ForeignKey(User, related_name="comment_likes", on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, related_name="likes", on_delete=models.CASCADE)

    class Meta:
        verbose_name = _("Comment like")
        verbose_name_plural = _("Comments likes")

    def __str__(self):
        return f"{self.author.pk} like for {self.comment.pk} comment."  # noqa


class Saved(models.Model):
    owner = models.ForeignKey(User, related_name="saved_posts", on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name="saved_by", on_delete=models.CASCADE)
    time_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = "-time_added", "-id"
        verbose_name = _("Saved post")
        verbose_name_plural = _("Saved posts")

    def __str__(self):
        return f"Saved post {self.post.pk} by {self.owner.pk}"  # noqa
