import typing

from dj_rest_auth.serializers import PasswordResetSerializer as PasswordResetSerializerCore
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import serializers

from users.forms import PasswordResetForm
from users.models import Follow
from users.services import PathImageTypeEnum
from users.tasks import make_center_crop

User = get_user_model()


class UserDefaultSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "id", "username", "avatar"


class UserCustomSerializer(serializers.ModelSerializer):
    posts_count = serializers.IntegerField()
    is_followed = serializers.BooleanField()
    followers_count = serializers.IntegerField()
    followings_count = serializers.IntegerField()

    class Meta:
        model = User
        fields = 'id', 'username', 'avatar', 'posts_count', 'is_followed', 'followers_count', 'followings_count'
        extra_kwargs = {
            'posts_count': {"allow_null": True},
            'is_followed': {"allow_null": True},
            'followers_count': {"allow_null": True},
            'followings_count': {"allow_null": True}
        }


#class UserCustomSerializer(serializers.Serializer):
    #id = serializers.IntegerField()
    #username = serializers.CharField()
    #avatar = serializers.CharField()
    #posts_count = serializers.IntegerField(allow_null=True)
    #is_followed = serializers.BooleanField(allow_null=True)
    #followers_count = serializers.IntegerField(allow_null=True)
    #followings_count = serializers.IntegerField(allow_null=True)


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "id", "username", "password", "email", "avatar", "timezone", "is_2fa_enabled"
        extra_kwargs = {
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
        is_avatar_updated = validated_data.get("avatar", instance.avatar) != instance.avatar
        instance.email = validated_data.get("email", instance.email)
        instance.avatar = validated_data.get("avatar", instance.avatar)
        instance.timezone = validated_data.get("timezone", instance.timezone)
        instance.is_2fa_enabled = validated_data.get("is_2fa_enabled", instance.is_2fa_enabled)
        instance.save()

        if is_avatar_updated:
            make_center_crop.delay(str(instance.avatar), PathImageTypeEnum.AVATAR)

        return instance


class FollowerSerializer(serializers.ModelSerializer):
    follower = UserDefaultSerializer(read_only=True)

    class Meta:
        model = Follow
        fields = "id", "follower"


class FollowingSerializer(serializers.ModelSerializer):
    following = UserDefaultSerializer(read_only=True)

    class Meta:
        model = Follow
        fields = "id", "following"

    def create(self, validated_data):
        follower = validated_data["follower"]
        following = validated_data["following"]

        filter = Follow.objects.filter(follower=follower, following=following)   # noqa

        if not filter.exists():
            return Follow.objects.create(follower=follower, following=following)   # noqa
        return filter.first()


class TokenSerializer(serializers.Serializer):
    token = serializers.CharField()


class DetailedCodeSerializer(serializers.Serializer):
    detail = serializers.CharField()
    code = serializers.CharField(max_length=32)


class PasswordResetSerializer(PasswordResetSerializerCore):
    def get_email_options(self) -> typing.Dict:
        return {
            "subject_template_name": 'users/mails/reset_password_body.html',
            "email_template_name": 'users/mails/reset_password_subject.html'
        }

    @property
    def password_reset_form_class(self) -> typing.Type[PasswordResetForm]:
        return PasswordResetForm


class TwoFactorAuthenticationCodeSerializer(serializers.Serializer):
    auth_code = serializers.CharField(
        max_length=settings.TWO_FACTOR_AUTHENTICATION_CODE_LENGTH,
        min_length=settings.TWO_FACTOR_AUTHENTICATION_CODE_LENGTH
    )
