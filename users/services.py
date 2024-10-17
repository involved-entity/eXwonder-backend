import secrets
import string
import enum
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.base import SessionBase
from rest_framework.authtoken.models import Token

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
    if path == settings.DEFAULT_USER_AVATAR_PATH:
        return path

    file = os.path.basename(path)
    name, extension = file.rsplit(".", 1)
    return os.path.join(image_type, f"{name}{settings.CROPPED_IMAGE_POSTFIX}.{extension}")


def get_user_login_token(user: User) -> str:
    token, _ = Token.objects.get_or_create(user=user)  # noqa

    return token.key


def remove_user_token(user: User) -> None:
    Token.objects.filter(user=user).delete()   # noqa
