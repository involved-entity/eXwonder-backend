import typing

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

User = get_user_model()


def send_mail_with_subject_and_body_as_html(
        subject_template: str,
        body_template: str,
        recipient_mail: str,
        context: typing.Optional[typing.Dict] = None
) -> None:
    subject = render_to_string(subject_template)
    html_message = render_to_string(body_template, context)
    plain_message = strip_tags(html_message)

    send_mail(
        subject,
        plain_message,
        None,
        [recipient_mail],
        fail_silently=True,
        html_message=html_message
    )
    return


@shared_task
def send_2fa_code_mail_message(email: str, code: int) -> None:
    send_mail_with_subject_and_body_as_html(
        "users/mails/2fa_code_subject.html",
        "users/mails/2fa_code_message.html",
        email,
        context={"code": code, "livetime": round(settings.TWO_FACTOR_AUTHENTICATION_CODE_LIVETIME / 60, 1)}
    )


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
