from rest_framework import serializers

from posts.models import Post, PostImage
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
        fields = "signature", "time_added", "images"
        extra_kwargs = {
            "time_added": {"read_only": True}
        }

    def create(self, validated_data):
        post = Post(
            author=validated_data["author"],
            signature=validated_data.get("signature", "")
        )
        post.save()

        images = self.context["request"].FILES.getlist("image")

        for image in list(images):
            post_image = PostImage(image=image, post=post)
            post_image.save()

        return post

    def get_time_added(self, post):
        return datetime_to_timezone(post.time_added, self.context["request"].user.timezone)
