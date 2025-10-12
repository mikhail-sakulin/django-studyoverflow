from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy
from users.services.domain import CustomUsernameValidator
from users.services.infrastructure import avatar_upload_to


class User(AbstractUser):
    username_validator = CustomUsernameValidator()

    username = models.CharField(
        verbose_name="Имя пользователя",
        max_length=150,
        unique=True,
        help_text=(
            "Имя пользователя должно быть не менее 4 символов и "
            "состоять только из латинских букв, цифр, символов '_' и '-'."
        ),
        validators=[username_validator],
        error_messages={
            "unique": gettext_lazy("A user with that username already exists."),
        },
    )

    avatar = models.ImageField(
        upload_to=avatar_upload_to,
        blank=True,
        default="avatars/default_avatar.jpg",
        verbose_name="Аватар",
    )
    bio = models.TextField(blank=True, verbose_name="Информация о пользователе")
    reputation = models.IntegerField(blank=True, default=0, verbose_name="Репутация")

    date_birth = models.DateTimeField(blank=True, null=True, verbose_name="Дата рождения")
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name="Время создания")
    time_update = models.DateTimeField(auto_now=True, verbose_name="Время изменения")

    def __str__(self):
        return self.username

    class Meta:
        ordering = ["username"]
