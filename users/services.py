import enum
import os
import secrets
import string
import typing

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.base import SessionBase
from django.db.models import Count, Exists, OuterRef, Q, QuerySet
from rest_framework.authtoken.models import Token

from users.models import Follow

User = get_user_model()


class PathImageTypeEnum(enum.StrEnum):
    POST = settings.POSTS_IMAGES_DIR
    AVATAR = settings.CUSTOM_USER_AVATARS_DIR


def make_2fa_authentication(session: SessionBase, user: User) -> str:
    code = "".join(secrets.choice(string.digits) for _ in range(settings.TWO_FACTOR_AUTHENTICATION_CODE_LENGTH))
    session["2fa_code"] = code
    session["2fa_code_user_id"] = user.pk
    session.set_expiry(settings.TWO_FACTOR_AUTHENTICATION_CODE_LIVETIME)
    return code


def get_upload_crop_path(path: str, image_type: PathImageTypeEnum) -> str:
    if settings.DEFAULT_USER_AVATAR_PATH in path:
        return path

    file = os.path.basename(path)
    name, extension = file.rsplit(".", 1)
    return os.path.join(image_type, f"{name}{settings.CROPPED_IMAGE_POSTFIX}.{extension}")


def get_user_login_token(user: User) -> str:
    token, _ = Token.objects.get_or_create(user=user)  # noqa

    return token.key


def annotate_users_queryset(user: User, queryset: QuerySet, fields: typing.Optional[typing.List] = None) -> QuerySet:
    if not fields:
        fields = ["posts_count", "is_followed", "followers_count", "followings_count"]

    annotate = {
        "posts_count": Count("posts", distinct=True) if "posts_count" in fields else None,
        "is_followed": Count("followers", distinct=True, filter=Q(followers__follower__pk=user.id))
        if "is_followed" in fields
        else None,
        "followers_count": Count("followers", distinct=True) if "followers_count" in fields else None,
        "followings_count": Count("following", distinct=True) if "followings_count" in fields else None,
    }

    queryset = queryset.annotate(**{key: value for key, value in annotate.items() if value})

    return queryset.order_by("-id" if "followers_count" not in fields else "-followers_count")


def annotate_follows_queryset(
    user: User, queryset: QuerySet, mode: typing.Literal["follower"] | typing.Literal["following"]
) -> QuerySet:
    user = user if isinstance(user, User) else user[0]
    queryset = queryset.prefetch_related(mode)
    annotate = {
        "posts_count": Count(mode + "__posts", distinct=True),
        "is_followed": Exists(Follow.objects.filter(follower_id=user.pk, following_id=OuterRef(mode + "__pk"))),  # noqa
        "followers_count": Count(mode + "__followers", distinct=True),
        "followings_count": Count(mode + "__following", distinct=True),
    }

    queryset = queryset.annotate(**annotate)

    return queryset.order_by("-followers_count")
