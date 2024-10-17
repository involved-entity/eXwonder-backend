import typing
import urllib.parse
from datetime import datetime

import pytz
from rest_framework import serializers
from django.conf import settings

from posts.models import Comment, Like, Post, PostImage
from users.serializers import UserSerializer
from users.tasks import make_center_crop
from users.services import PathImageTypeEnum, get_upload_crop_path


def datetime_to_timezone(dt: datetime, timezone: str, attribute_name: typing.Optional[str] = 'time_added') \
        -> typing.Dict:
    dt = pytz.timezone(timezone).localize(datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second))
    return {
        attribute_name: (dt + dt.utcoffset()).strftime("%d/%m/%Y %H:%M"),
        "timezone": timezone
    }


class PostImageSerializer(serializers.ModelSerializer):
    image_crop = serializers.SerializerMethodField()

    class Meta:
        model = PostImage
        fields = "id", "image", "image_crop"
        read_only_fields = "image",

    def get_image_crop(self, instance):
        media_url = urllib.parse.urljoin(settings.HOST, settings.MEDIA_URL)
        return urllib.parse.urljoin(media_url, get_upload_crop_path(str(instance.image), PathImageTypeEnum.POST))


class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    images = PostImageSerializer(many=True, read_only=True)
    time_added = serializers.SerializerMethodField(read_only=True)

    likes_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Post
        fields = "id", "author", "signature", "time_added", "images", "likes_count", "comments_count"

    def validate(self, attrs):
        if "image0" in list(self.context["request"].data.keys()):
            return attrs
        raise serializers.ValidationError("Images are none.", code="invalid")

    def create(self, validated_data):
        header_image = None
        post_images = []

        post = Post(
            author=validated_data["author"],
            signature=validated_data.get("signature", "")
        )
        post.save()

        for key, value in self.context["request"].data.items():
            if key.startswith("image"):
                instance = PostImage(image=value, post=post)
                if key == 'image0':
                    header_image = instance
                post_images.append(PostImage(image=value, post=post))

        PostImage.objects.bulk_create(post_images)   # noqa
        make_center_crop.delay(str(header_image.image), PathImageTypeEnum.POST)
        return post

    def get_time_added(self, post):
        return datetime_to_timezone(post.time_added, self.context["request"].user.timezone)


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = "id", "author", "post"
        read_only_fields = "author", "post"

    def create(self, validated_data):
        like = Like.objects.filter(author=validated_data["author"], post=validated_data["post"])   # noqa
        if like.exists():
            return like.first()
        return super().create(validated_data)


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = "id", "author", "post", "comment"
        read_only_fields = "post",


class PostIDSerializer(serializers.Serializer):
    post_id = serializers.IntegerField(min_value=1)
