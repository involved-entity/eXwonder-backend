import secrets
import string

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.base import SessionBase
from rest_framework.authtoken.models import Token

User = get_user_model()


def make_2fa_authentication(session: SessionBase, user: User) -> str:
    code = "".join(secrets.choice(string.digits) for _ in range(settings.TWO_FACTOR_AUTHENTICATION_CODE_LENGTH))
    session["2fa_code"] = code
    session["2fa_code_user_id"] = user.pk
    session.set_expiry(settings.TWO_FACTOR_AUTHENTICATION_CODE_LIVETIME)
    return code


def get_user_login_token(user: User) -> str:
    token, _ = Token.objects.get_or_create(user=user)  # noqa

    return token.key
