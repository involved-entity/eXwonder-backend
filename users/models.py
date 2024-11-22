from typing import Optional

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import MinLengthValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


def get_uploaded_avatar_path(instance: Optional["ExwonderUser"] = None, filename: Optional[str] = None) -> str:
    return f"{settings.CUSTOM_USER_AVATARS_DIR}/{filename}"


class ExwonderUserManager(BaseUserManager):
    def create_user(
        self, username: str, email: str, avatar: str, timezone: str, password: Optional[str] = None
    ) -> "ExwonderUser":
        user: "ExwonderUser" = self.model(
            username=username, email=self.normalize_email(email) or None, avatar=avatar, timezone=timezone
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        username: str,
        email: Optional[str] = None,
        avatar: Optional[str] = None,
        timezone: Optional[str] = None,
        password: Optional[str] = None,
    ) -> "ExwonderUser":
        user = self.create_user(
            username=username,
            email=email or "",
            avatar=avatar or settings.DEFAULT_USER_AVATAR_PATH,
            timezone=timezone or settings.DEFAULT_USER_TIMEZONE,
            password=password,
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class ExwonderUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(
        verbose_name=_("Username"),
        max_length=16,
        unique=True,
        validators=[UnicodeUsernameValidator(), MinLengthValidator(5)],
        error_messages={
            "unique": _("Username isn't unique."),
        },
    )
    email = models.EmailField(verbose_name=_("Email"), unique=True, null=True)
    avatar = models.ImageField(
        verbose_name=_("Avatar"), upload_to=get_uploaded_avatar_path, default=settings.DEFAULT_USER_AVATAR_PATH
    )
    timezone = models.CharField(verbose_name=_("Time zone"), max_length=64, default=settings.DEFAULT_USER_TIMEZONE)
    date_joined = models.DateTimeField(verbose_name=_("Date joined"), auto_now_add=True)
    penultimate_login = models.DateTimeField(verbose_name=_("Penultimate login"), blank=True, null=True)
    is_2fa_enabled = models.BooleanField(verbose_name=_("Is 2FA enabled"), default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(
        _("Staff status"),
        default=False,
    )

    USERNAME_FIELD = "username"
    objects = ExwonderUserManager()

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

        ordering = ("pk",)

        db_table = "exwonder_users"

        indexes = (models.Index(fields=("username",), name="Username index"),)

    def __str__(self):
        return f"{self.username}"


class Follow(models.Model):
    follower = models.ForeignKey(ExwonderUser, related_name="following", on_delete=models.CASCADE)
    following = models.ForeignKey(ExwonderUser, related_name="followers", on_delete=models.CASCADE)

    class Meta:
        ordering = ("-pk",)
        verbose_name = _("Follow")
        verbose_name_plural = _("Follows")

    def __str__(self):
        return f"{self.follower.pk} following for {self.following.pk}"  # noqa
