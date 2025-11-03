from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy
from users.services.domain import (
    generate_new_filename_with_uuid,
)
from users.services.infrastructure import (
    AvatarFileValidator,
    CustomUsernameValidator,
    PersonalNameValidator,
    delete_old_avatar_names,
    generate_avatar_small,
    generate_default_avatar_in_different_sizes,
    get_old_avatar_names,
)


class User(AbstractUser):
    # Константы
    DEFAULT_AVATAR_FILENAME = "avatars/default_avatar.jpg"
    DEFAULT_AVATAR_SMALL_SIZE1_FILENAME = "avatars/default_avatar_small_size1.jpg"
    DEFAULT_AVATAR_SMALL_SIZE2_FILENAME = "avatars/default_avatar_small_size2.jpg"
    DEFAULT_AVATAR_SMALL_SIZE3_FILENAME = "avatars/default_avatar_small_size3.jpg"
    AVATAR_SMALL_SIZES = {
        "size1": (100, 100),
        "size2": (170, 170),
        "size3": (800, 800),
    }

    # Валидаторы
    username_validator = CustomUsernameValidator()
    first_name_last_name_validator = PersonalNameValidator()
    avatar_validator = AvatarFileValidator()

    # Поля модели
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
        default=DEFAULT_AVATAR_FILENAME,
        validators=[avatar_validator],
        verbose_name="Аватар",
    )

    avatar_small_size1 = models.ImageField(
        blank=True, default=DEFAULT_AVATAR_SMALL_SIZE1_FILENAME, verbose_name="Миниатюра аватара №1"
    )
    avatar_small_size2 = models.ImageField(
        blank=True, default=DEFAULT_AVATAR_SMALL_SIZE2_FILENAME, verbose_name="Миниатюра аватара №2"
    )
    avatar_small_size3 = models.ImageField(
        blank=True, default=DEFAULT_AVATAR_SMALL_SIZE3_FILENAME, verbose_name="Миниатюра аватара №3"
    )

    bio = models.TextField(blank=True, verbose_name="Информация о пользователе")

    date_birth = models.DateField(blank=True, null=True, verbose_name="Дата рождения")
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name="Время создания аккаунта")

    reputation = models.IntegerField(default=0, verbose_name="Репутация")
    posts_count = models.PositiveIntegerField(default=0, verbose_name="Количество постов")
    comments_count = models.PositiveIntegerField(default=0, verbose_name="Количество комментариев")

    last_seen = models.DateTimeField(
        null=True,
        verbose_name="Был в сети",
    )

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

        # Если пользовательский аватар удален, то self.avatar.name == ""
        is_avatar_deleted = not self.avatar

        # avatar и avatar_small создаются только при условии, что avatar поменялся,
        # при создании нового объекта is_avatar_changed == False
        if is_avatar_changed:
            if is_avatar_deleted:
                # Если пользовательский аватар удален, то ему присваиваются стандартные аватары
                self.avatar.name = self._meta.get_field("avatar").get_default()
                avatar_small_size1_name = self._meta.get_field("avatar_small_size1").get_default()
                avatar_small_size2_name = self._meta.get_field("avatar_small_size2").get_default()
                avatar_small_size3_name = self._meta.get_field("avatar_small_size3").get_default()
            else:
                # Создание avatar.name с помощью uuid
                avatar_name = generate_new_filename_with_uuid(self.avatar.name)

                # Полное имя для avatar в хранилище
                self.avatar.name = f"avatars/{self.pk}/{avatar_name}"

                # Создание avatar_small и получение имен файлов
                avatar_small_size1_name = generate_avatar_small(self, size_type=1)
                avatar_small_size2_name = generate_avatar_small(self, size_type=2)
                avatar_small_size3_name = generate_avatar_small(self, size_type=3)

            # Если avatar_small_name == False, значит avatar_small не создается
            if avatar_small_size1_name:
                self.avatar_small_size1.name = avatar_small_size1_name

            if avatar_small_size2_name:
                self.avatar_small_size2.name = avatar_small_size2_name

            if avatar_small_size3_name:
                self.avatar_small_size3.name = avatar_small_size3_name

        super().save(*args, **kwargs)

        if is_avatar_changed or is_avatar_deleted:
            # Удаление старых файлов avatar, если они не были default
            if old_avatar_names.old_avatar_name != self._meta.get_field("avatar").get_default():
                delete_old_avatar_names(old_avatar_names)

    @classmethod
    def generate_default_avatar_different_sizes(cls):
        """
        Генерирует уменьшенные версии стандартного аватара default_avatar
        для всех размеров, указанных в AVATAR_SMALL_SIZES.
        """
        generate_default_avatar_in_different_sizes(cls)

    def __str__(self):
        return self.username

    class Meta:
        ordering = ["username"]
