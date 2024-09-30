from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "id", "username", "password", "email", "avatar", "timezone", "is_2fa_enabled"
        extra_kwargs = {
            "id": {"read_only": True},
            "password": {"write_only": True},
            "email": {"required": False},
            "avatar": {"required": False},
            "timezone": {"required": False},
        }

    def create(self, validated_data):
        user = User(
            username=validated_data["username"],
            email=validated_data.get("email", None),
            avatar=validated_data.get("avatar", settings.DEFAULT_USER_AVATAR_PATH),
            timezone=validated_data.get("timezone", settings.DEFAULT_USER_TIMEZONE)
        )
        user.set_password(validated_data["password"])
        user.save()
        return user

    def update(self, instance, validated_data):
        instance.email = validated_data.get("email", instance.email)
        instance.avatar = validated_data.get("avatar", instance.avatar)
        instance.timezone = validated_data.get("timezone", instance.timezone)
        instance.is_2fa_enabled = validated_data.get("is_2fa_enabled", instance.is_2fa_enabled)
        instance.save()
        return instance
