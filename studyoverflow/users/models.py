from celery import chain
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models, transaction
from django.db.models import Q
from django.utils.translation import gettext_lazy
from users.services.domain import (
    generate_new_filename_with_uuid,
)
from users.services.infrastructure import (
    AvatarFileValidator,
    CustomUsernameValidator,
    PersonalNameValidator,
    generate_default_avatar_in_different_sizes,
    get_old_avatar_names,
)
from users.tasks import delete_old_avatars_from_s3_storage, generate_and_save_avatars_small


class CustomUserManager(UserManager):
    def get_by_natural_key(self, username_or_email):
        return self.get(Q(username=username_or_email) | Q(email__iexact=username_or_email))


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

    email = models.EmailField(unique=True, verbose_name=gettext_lazy("email address"))

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

    objects = CustomUserManager()

    def save(self, *args, skip_celery_task=False, **kwargs):
        is_avatar_deleted = False
        is_avatar_changed = False

        # Сохранение старых имен файлов для avatar перед save() для их
        # последующего удаления
        old_avatar_names = get_old_avatar_names(self)

        if self.pk:
            is_avatar_deleted = not self.avatar

            if is_avatar_deleted:
                # Если пользовательский аватар удален, то ему присваивается
                # стандартный аватар и миниатюры
                self.avatar.name = self._meta.get_field("avatar").get_default()
                self.avatar_small_size1.name = self._meta.get_field(
                    "avatar_small_size1"
                ).get_default()
                self.avatar_small_size2.name = self._meta.get_field(
                    "avatar_small_size2"
                ).get_default()
                self.avatar_small_size3.name = self._meta.get_field(
                    "avatar_small_size3"
                ).get_default()

            else:
                is_avatar_changed = self.avatar.name != old_avatar_names.old_avatar_name

                if is_avatar_changed:
                    # Создание avatar.name с помощью uuid
                    avatar_name_file = generate_new_filename_with_uuid(self.avatar.name)

                    # Полное имя для avatar в хранилище
                    self.avatar.name = f"avatars/{self.pk}/{avatar_name_file}"

        super().save(*args, **kwargs)

        if skip_celery_task:
            return

        if is_avatar_changed:
            # цепочка celery задач на создание миниатюр и удаление
            tasks = chain(
                generate_and_save_avatars_small.si(self.pk),
                delete_old_avatars_from_s3_storage.si(self.pk, list(old_avatar_names)),
            )

            # Запуск задач только после завершения сохранения в БД
            transaction.on_commit(lambda: tasks.apply_async())

        elif (
            is_avatar_deleted
            and old_avatar_names.old_avatar_name != self._meta.get_field("avatar").get_default()
        ):
            # celery задача на удаление после завершения сохранения в БД
            transaction.on_commit(
                lambda: delete_old_avatars_from_s3_storage.delay(self.pk, list(old_avatar_names))
            )

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
