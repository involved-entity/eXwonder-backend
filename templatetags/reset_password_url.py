import os

from django import template
from environ import Env

from core.settings import BASE_DIR

env = Env()
Env.read_env(os.path.join(BASE_DIR, ".env"))

register = template.Library()


def reset_password_url(uid: str, token: str) -> str:
    return f'http://{env("PASSWORD_RESET_URL", default="localhost:80")}/reset-password/?uid={uid}&token={token}'


register.simple_tag(reset_password_url)
