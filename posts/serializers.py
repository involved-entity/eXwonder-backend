import typing
from datetime import datetime

import pytz
from rest_framework import serializers

from posts.models import Comment, Like, Post, PostImage
from users.serializers import UserSerializer


def datetime_to_timezone(dt: datetime, timezone: str, attribute_name: typing.Optional[str] = 'time_added') \
        -> typing.Dict:
    dt = pytz.timezone(timezone).localize(datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second))
    return {
        attribute_name: (dt + dt.utcoffset()).strftime("%d/%m/%Y %H:%M"),
        "timezone": timezone
    }


class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = "id", "image"
        read_only_fields = "image",


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
        for key, value in self.context["request"].data.items():
            if key.startswith("image"):
                return attrs
        raise serializers.ValidationError("Images are none.", code="invalid")

    def create(self, validated_data):
        post = Post(
            author=validated_data["author"],
            signature=validated_data.get("signature", "")
        )
        post.save()

        for key, value in self.context["request"].data.items():
            if key.startswith("image"):
                post_image = PostImage(image=value, post=post)
                post_image.save()

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
