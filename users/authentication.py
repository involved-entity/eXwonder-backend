import pytz
from django.conf import settings
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication as CoreTokenAuthnetication
from rest_framework.authtoken.models import Token


class TokenAuthentication(CoreTokenAuthnetication):
    def authenticate_credentials(self, key):
        user, token = super().authenticate_credentials(key)

        utc = timezone.now().replace(tzinfo=pytz.utc)

        if token.created < (utc - settings.TOKEN_EXP_TIME):
            token.delete()
            token = Token.objects.create(user=user)  # noqa

        if not user.last_login or user.last_login < (utc - settings.LAST_LOGIN_UPDATE_TIME):
            user.penultimate_login = user.last_login
            user.last_login = utc
            user.save()

        return user, token
