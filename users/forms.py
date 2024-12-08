import typing

from django import forms
from django.contrib.auth.forms import PasswordResetForm as PasswordResetFormCore
from django.utils.text import gettext_lazy as _

from users.tasks import send_reset_password_mail


class PasswordResetForm(PasswordResetFormCore):
    email = forms.EmailField(
        label=_("Почта"),
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "Пароль для сброса"}),
    )

    def send_mail(
        self,
        subject_template_name: str,
        email_template_name: str,
        context: typing.Dict[str, typing.Any],
        from_email: typing.Union[str, None],
        to_email: str,
        html_email_template_name: typing.Optional[str] = None,
    ) -> None:
        context["user"] = context["user"].id

        send_reset_password_mail.apply_async(
            args=[subject_template_name, email_template_name, context, from_email, to_email, html_email_template_name],
            queue="normal_priority",
        )
