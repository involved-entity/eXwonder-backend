import typing

from celery import shared_task
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm

User = get_user_model()


@shared_task
def send_reset_password_mail(
        subject_template_name: str,
        email_template_name: str,
        context: typing.Dict[str, typing.Any],
        from_email: typing.Union[str, None],
        to_email: str,
        html_email_template_name: typing.Optional[str] = None
) -> None:
    context['user'] = User.objects.get(pk=context['user'])

    PasswordResetForm().send_mail(
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name
    )
    return
