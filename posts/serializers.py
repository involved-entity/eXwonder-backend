import typing
import urllib.parse
from datetime import datetime

import pytz
from django.conf import settings
from django.db import transaction
from django.utils.timesince import timesince
from rest_framework import serializers

from posts.models import Comment, CommentLike, Post, PostImage, PostLike, Saved, Tag
from posts.services import extract_post_images_from_request_data, get_or_create_tags
from users.serializers import UserDefaultSerializer
from users.services import PathImageTypeEnum, get_upload_crop_path
from users.tasks import make_center_crop
from notifications.tasks import send_notifications


def datetime_to_timezone(
    dt: datetime, timezone: str, attribute_name: typing.Optional[str] = "time_added"
) -> typing.Dict:
    dt = pytz.timezone(timezone).localize(datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second))
    return {attribute_name: timesince(dt + dt.utcoffset()), "timezone": timezone}


class PostImageSerializer(serializers.ModelSerializer):
    image_crop = serializers.SerializerMethodField()

    class Meta:
        model = PostImage
        fields = "id", "image", "image_crop"
        read_only_fields = ("image",)

    def get_image_crop(self, instance):
        media_url = urllib.parse.urljoin(settings.HOST, settings.MEDIA_URL)
        return urllib.parse.urljoin(media_url, get_upload_crop_path(str(instance.image), PathImageTypeEnum.POST))


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("name",)


class PostRequestSerializer(serializers.ModelSerializer):
    author = UserDefaultSerializer(read_only=True)
    images = PostImageSerializer(many=True, read_only=True)

    tags = serializers.CharField(required=False)

    class Meta:
        model = Post
        fields = (
            "id",
            "author",
            "signature",
            "time_added",
            "images",
            "tags",
        )
        read_only_fields = ("time_added",)

    def validate(self, attrs):
        if "image0" not in list(self.context["request"].data.keys()):
            raise serializers.ValidationError("No main image for post. Pass it in the 'image0' key.", code="invalid")

        tags = self.context["request"].data.get("tags", "").split(",")
        invalid_tags = [tag for tag in tags if len(tag) > 32]

        if invalid_tags:
            raise serializers.ValidationError(
                f"Invalid length for tags: '{','.join(invalid_tags)}' tag.", code="invalid"
            )

        return attrs

    def create(self, validated_data):
        tags = self.context["request"].data.get("tags", "")

        with transaction.atomic():
            post = Post(author=validated_data["author"], signature=validated_data.get("signature", ""))
            post.save()
            post_images = extract_post_images_from_request_data(post, self.context["request"].data)
            post_images = PostImage.objects.bulk_create(post_images)  # noqa
            if len(tags):
                tags = get_or_create_tags(tags.split(","))
                post.tags.add(*tags)

        make_center_crop.apply_async(args=[str(post_images[0].image), PathImageTypeEnum.POST], queue="high_priority")
        send_notifications.apply_async(args=[post.pk], queue="low_priority")

        return post


class PostResponseSerializer(serializers.ModelSerializer):
    author = UserDefaultSerializer(read_only=True)
    images = PostImageSerializer(many=True, read_only=True)
    time_added = serializers.SerializerMethodField(read_only=True)

    likes_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)
    is_liked = serializers.BooleanField(read_only=True)
    is_commented = serializers.BooleanField(read_only=True)
    is_saved = serializers.BooleanField(read_only=True)

    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = (
            "id",
            "author",
            "signature",
            "time_added",
            "images",
            "tags",
            "likes_count",
            "comments_count",
            "is_liked",
            "is_commented",
            "is_saved",
        )

    def get_time_added(self, post):
        return datetime_to_timezone(post.time_added, self.context["request"].user.timezone)


class PostLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostLike
        fields = "id", "author", "post"
        read_only_fields = "author", "post"

    def create(self, validated_data):
        like = PostLike.objects.filter(author=validated_data["author"], post=validated_data["post"])  # noqa
        if like.exists():
            return like.first()
        return super().create(validated_data)


class CommentSerializer(serializers.ModelSerializer):
    author = UserDefaultSerializer(read_only=True)
    time_added = serializers.SerializerMethodField()

    likes_count = serializers.IntegerField(read_only=True)
    is_liked = serializers.BooleanField(read_only=True)

    class Meta:
        model = Comment
        fields = "id", "author", "post", "comment", "time_added", "likes_count", "is_liked"
        read_only_fields = "post", "time_added"

    def get_time_added(self, comment):
        return datetime_to_timezone(comment.time_added, self.context["request"].user.timezone)


class CommentLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentLike
        fields = "id", "author", "comment"
        read_only_fields = "author", "comment"

    def create(self, validated_data):
        like = CommentLike.objects.filter(author=validated_data["author"], comment=validated_data["comment"])  # noqa
        if like.exists():
            return like.first()
        return super().create(validated_data)


class SavedSerializer(serializers.ModelSerializer):
    owner = UserDefaultSerializer(read_only=True)
    post = PostResponseSerializer(required=False)

    likes_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)
    is_liked = serializers.BooleanField(read_only=True)
    is_commented = serializers.BooleanField(read_only=True)
    is_saved = serializers.BooleanField(read_only=True)

    class Meta:
        model = Saved
        fields = (
            "id",
            "owner",
            "post",
            "time_added",
            "likes_count",
            "comments_count",
            "is_liked",
            "is_commented",
            "is_saved",
        )
        read_only_fields = "post", "time_added"

    def get_time_added(self, saved):
        return datetime_to_timezone(saved.time_added, self.context["request"].user.timezone)


class PostIDSerializer(serializers.Serializer):
    post_id = serializers.IntegerField(min_value=1)


class CommentIDSerializer(serializers.Serializer):
    comment_id = serializers.IntegerField(min_value=1)
