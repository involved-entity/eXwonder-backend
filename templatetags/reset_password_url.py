from django import template

register = template.Library()


def reset_password_url(uid: str, token: str) -> str:
    return f'http://localhost:5173/reset-password/?uid={uid}&token={token}'

register.simple_tag(reset_password_url)

