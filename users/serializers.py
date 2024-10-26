import typing
import urllib.parse

from dj_rest_auth.serializers import PasswordResetSerializer as PasswordResetSerializerCore
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import serializers
import pytz

from users.forms import PasswordResetForm
from users.models import Follow
from users.services import PathImageTypeEnum, get_upload_crop_path
from users.tasks import make_center_crop

User = get_user_model()


class UserAvatarField(serializers.ImageField):
    def to_representation(self, value):
        media_url = urllib.parse.urljoin(settings.HOST, settings.MEDIA_URL)
        return urllib.parse.urljoin(media_url, get_upload_crop_path(str(value), PathImageTypeEnum.AVATAR))


class UserDefaultSerializer(serializers.ModelSerializer):
    avatar = UserAvatarField()

    class Meta:
        model = User
        fields = "id", "username", "avatar"


class UserCustomSerializer(serializers.ModelSerializer):
    avatar = UserAvatarField()

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


class UserDetailSerializer(serializers.ModelSerializer):
    avatar = UserAvatarField(required=False)

    class Meta:
        model = User
        fields = "id", "username", "password", "email", "avatar", "timezone", "is_2fa_enabled"
        extra_kwargs = {
            "password": {"write_only": True},
            "email": {"required": False},
            "avatar": {"required": False},
            "timezone": {"required": False},
        }

    def validate_timezone(self, value):
        if value:
            if value in pytz.common_timezones_set:
                return value
            raise serializers.ValidationError('Invalid timezone')
        return value

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


class DetailedCodeSessionKeySerializer(serializers.Serializer):
    detail = serializers.CharField()
    code = serializers.CharField()
    session_key = serializers.CharField()


class UserDetailTimezonesSerializer(serializers.Serializer):
    user = UserDetailSerializer(read_only=True)
    availible_timezones = serializers.ListField()


class FollowerCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = "id", "follower"


class FollowingCreateSerializer(serializers.ModelSerializer):
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


class FollowerSerializer(serializers.ModelSerializer):
    follower = UserDefaultSerializer()
    posts_count = serializers.IntegerField()
    is_followed = serializers.BooleanField()
    followers_count = serializers.IntegerField()
    followings_count = serializers.IntegerField()

    class Meta:
        model = Follow
        fields = "id", "follower", "posts_count", "is_followed", "followers_count", "followings_count"


class FollowingSerializer(serializers.ModelSerializer):
    following = UserDefaultSerializer()
    posts_count = serializers.IntegerField()
    is_followed = serializers.BooleanField()
    followers_count = serializers.IntegerField()
    followings_count = serializers.IntegerField()

    class Meta:
        model = Follow
        fields = "id", "following", "posts_count", "is_followed", "followers_count", "followings_count"


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
    session_key = serializers.CharField()
