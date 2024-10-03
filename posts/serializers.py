from rest_framework import serializers

from posts.models import Like, Post, PostImage
from posts.services import datetime_to_timezone


class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = "image",


class PostSerializer(serializers.ModelSerializer):
    images = PostImageSerializer(many=True, read_only=True)
    time_added = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = "id", "author", "signature", "time_added", "images"
        extra_kwargs = {
            "time_added": {"read_only": True},
            "author": {"read_only": True},
        }

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
        fields = "author", "post"
        extra_kwargs = {
            "author": {"read_only": True},
            "post": {"read_only": True}
        }

    def create(self, validated_data):
        like = Like(
            author=validated_data["author"],
            post=validated_data["post"]
        )
        like.save()

        return like
