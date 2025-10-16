from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy
from users.services.domain import CustomUsernameValidator, PersonalNameValidator
from users.services.infrastructure import avatar_upload_to, generate_avatar_small


class User(AbstractUser):
    username_validator = CustomUsernameValidator()
    first_name_last_name_validator = PersonalNameValidator()

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

    first_name = models.CharField(
        max_length=150, blank=True, validators=[first_name_last_name_validator], verbose_name="Имя"
    )
    last_name = models.CharField(
        max_length=150,
        blank=True,
        validators=[first_name_last_name_validator],
        verbose_name="Фамилия",
    )

    avatar = models.ImageField(
        upload_to=avatar_upload_to,
        blank=True,
        default="avatars/default_avatar.jpg",
        verbose_name="Аватар",
    )

    avatar_small = models.ImageField(blank=True, verbose_name="Миниатюра аватара")

    bio = models.TextField(blank=True, verbose_name="Информация о пользователе")
    reputation = models.IntegerField(blank=True, default=0, verbose_name="Репутация")

    date_birth = models.DateTimeField(blank=True, null=True, verbose_name="Дата рождения")
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name="Время создания")
    time_update = models.DateTimeField(auto_now=True, verbose_name="Время изменения")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Создание avatar_small и получение имени файла
        name_avatar_small = generate_avatar_small(self)

        # Если name_avatar_small == False, значит возникла ошибка, тогда
        # avatar_small не создается
        if not name_avatar_small:
            return

        # Если нужный avatar_small уже сгенерирован (avatar не менялся),
        # то повторного сохранения не происходит
        if self.avatar_small.name != name_avatar_small:
            self.avatar_small.name = name_avatar_small
            super().save(update_fields=["avatar_small"])

    def __str__(self):
        return self.username

    class Meta:
        ordering = ["username"]
