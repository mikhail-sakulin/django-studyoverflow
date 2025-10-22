from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy
from users.services.domain import (
    CustomUsernameValidator,
    PersonalNameValidator,
    generate_new_filename_with_uuid,
)
from users.services.infrastructure import (
    delete_old_avatar_names,
    generate_avatar_small,
    get_old_avatar_names,
)


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
        """
        Переопределение save() для:
            - генерации уменьшенных версий avatar
            - удаления устаревших файлов
        """
        # Сохранение старых имен файлов для avatar перед save() для их
        # последующего удаления
        old_avatar_names = get_old_avatar_names(self)

        # False, если аватар не менялся, или создается новый пользователь,
        # True, если аватар менялся
        is_avatar_changed = (
            old_avatar_names.old_avatar_name is not None
            and old_avatar_names.old_avatar_name != self.avatar.name
        )

        # avatar и avatar_small создаются только при условии, что avatar поменялся,
        # при создании нового объекта is_avatar_changed == False
        if is_avatar_changed:
            # Создание avatar.name с помощью uuid
            avatar_name = generate_new_filename_with_uuid(self.avatar.name)

            # Полное имя для avatar в хранилище
            self.avatar.name = f"avatars/{self.pk}/{avatar_name}"

            # Создание avatar_small и получение имени файла
            avatar_small_name = generate_avatar_small(self)

            # Если name_avatar_small == False, значит avatar_small не создается
            if avatar_small_name:
                self.avatar_small.name = avatar_small_name

        super().save(*args, **kwargs)

        if is_avatar_changed:
            # Удаление старых файлов avatar
            delete_old_avatar_names(old_avatar_names)

    def __str__(self):
        return self.username

    class Meta:
        ordering = ["username"]
