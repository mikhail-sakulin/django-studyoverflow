from celery import chain
from django.contrib.auth.models import AbstractUser, Group, UserManager
from django.db import models, transaction
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy
from users.services.infrastructure import (
    AvatarFileValidator,
    CustomUsernameValidator,
    PersonalNameValidator,
    generate_default_avatar_in_different_sizes,
    get_old_avatar_names,
    user_avatar_upload_path,
)
from users.tasks import delete_old_avatars_from_s3_storage, generate_and_save_avatars_small


class CustomUserManager(UserManager):
    def get_by_natural_key(self, username_or_email):
        return self.get(Q(username=username_or_email) | Q(email__iexact=username_or_email))


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Администратор"
        MODERATOR = "MODERATOR", "Модератор"
        STAFF_VIEWER = "STAFF_VIEWER", "Персонал (просмотр)"
        USER = "USER", "Пользователь"

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

    ROLE_FLAGS_MAP = {
        Role.ADMIN: {"is_staff": True, "is_superuser": True},
        Role.MODERATOR: {"is_staff": True, "is_superuser": False},
        Role.STAFF_VIEWER: {"is_staff": True, "is_superuser": False},
        Role.USER: {"is_staff": False, "is_superuser": False},
    }
    ROLE_GROUPS_MAP = {
        Role.MODERATOR: ["Moderators", "StaffViewers"],
        Role.STAFF_VIEWER: ["StaffViewers"],
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
        upload_to=user_avatar_upload_path,
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
        default=timezone.now,
        verbose_name="Был в сети",
    )

    is_social = models.BooleanField(default=False, verbose_name="Через соцсеть")

    is_blocked = models.BooleanField(default=False, verbose_name="Заблокирован")
    blocked_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата и время блокировки")
    blocked_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="blocked_users",
        verbose_name="Кем заблокирован",
    )

    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.USER, verbose_name="Роль"
    )

    objects = CustomUserManager()

    def __str__(self):
        return self.username

    class Meta:
        ordering = ["username"]
        permissions = [
            ("block_user", "Can block/unblock users"),
        ]

    def get_absolute_url(self):
        return reverse("users:profile", kwargs={"username": self.username})

    @property
    def is_admin(self):
        return self.is_superuser

    @property
    def is_moderator(self):
        return self.role == self.Role.MODERATOR

    @property
    def is_staff_viewer(self):
        return self.role == self.Role.STAFF_VIEWER

    @property
    def is_user(self):
        return self.role == self.Role.USER

    def save(self, *args, **kwargs):
        is_creation = not self.pk
        update_fields = kwargs.get("update_fields")

        if not update_fields or "role" in update_fields:
            self._sync_role_flags()

        post_save_context = {}
        if not is_creation and (not update_fields or "avatar" in update_fields):
            post_save_context = self._handle_update_avatar()

        with transaction.atomic():
            super().save(*args, **kwargs)

            if not update_fields or "role" in update_fields:
                self._sync_role_groups()

        if is_creation:
            self._schedule_creation_celery_tasks()
        elif post_save_context:
            self._schedule_update_celery_tasks(post_save_context)

    def _sync_role_flags(self):
        """
        Синхронизирует системные флаги и роль.
        Устанавливает is_staff и is_superuser на основе выбранной роли.
        """
        if self.is_superuser and not self.pk:
            self.role = self.Role.ADMIN

        flags = self.ROLE_FLAGS_MAP.get(self.role)

        if flags:
            for field, value in flags.items():
                setattr(self, field, value)

    def _sync_role_groups(self):
        """
        Назначает или удаляет группы "Moderators" и "StaffViewers".
        """
        managed_group_names = ["Moderators", "StaffViewers"]
        target_group_names = set(self.ROLE_GROUPS_MAP.get(self.role, []))

        current_managed_group_names = set(
            self.groups.filter(name__in=managed_group_names).values_list("name", flat=True)
        )

        groups_to_add = target_group_names - current_managed_group_names
        groups_to_remove = current_managed_group_names - target_group_names

        if groups_to_remove:
            self.groups.remove(*Group.objects.filter(name__in=groups_to_remove))

        if groups_to_add:
            for group_name in groups_to_add:
                group, _ = Group.objects.get_or_create(name=group_name)
                self.groups.add(group)

    def _handle_update_avatar(self):
        """
        Обрабатывает изменения аватара перед обновлением.
        Возвращает словарь с флагами и данными для пост-обработки.
        """
        avatar_name_in_db, avatar_names_for_delete = get_old_avatar_names(self)
        default_avatar = self._meta.get_field("avatar").get_default()

        is_deleted = not self.avatar
        is_new_upload = not is_deleted and self.avatar != avatar_name_in_db

        if is_deleted:
            # Сброс на дефолт
            self.avatar = default_avatar
            self._reset_small_avatars(default=True)

        elif is_new_upload:
            # Удаление миниатюр, так как основной аватар изменился
            self._reset_small_avatars(default=False)

        return {
            "is_new_upload": is_new_upload,
            "is_deleted": is_deleted,
            "avatar_names_for_delete": avatar_names_for_delete,
            "was_default": avatar_name_in_db == default_avatar,
        }

    def _reset_small_avatars(self, default: bool):
        for field_name in self.get_small_avatar_fields():
            if default:
                value = self._meta.get_field(field_name).get_default()
            else:
                value = None
            setattr(self, field_name, value)

    def _schedule_creation_celery_tasks(self):
        """Задачи Celery при создании пользователя."""
        default_avatar = self._meta.get_field("avatar").get_default()
        if self.avatar != default_avatar:
            transaction.on_commit(lambda: generate_and_save_avatars_small.delay(self.pk))

    def _schedule_update_celery_tasks(self, context: dict):
        """Задачи Celery при обновлении пользователя."""
        if not context:
            return

        is_new_upload = context.get("is_new_upload")
        is_deleted = context.get("is_deleted")
        avatar_names_for_delete = context.get("avatar_names_for_delete")
        was_default = context.get("was_default")

        if is_new_upload:
            # цепочка celery задач на создание миниатюр и удаление
            tasks = chain(
                generate_and_save_avatars_small.si(self.pk),
                delete_old_avatars_from_s3_storage.si(self.pk, list(avatar_names_for_delete or [])),
            )

            # Запуск задач только после завершения сохранения в БД
            transaction.on_commit(lambda: tasks.apply_async())

        elif is_deleted and not was_default:
            # celery задача на удаление после завершения сохранения в БД
            transaction.on_commit(
                lambda: delete_old_avatars_from_s3_storage.delay(
                    self.pk, list(avatar_names_for_delete or [])
                )
            )

    @classmethod
    def generate_default_avatar_different_sizes(cls):
        """
        Генерирует уменьшенные версии стандартного аватара default_avatar
        для всех размеров, указанных в AVATAR_SMALL_SIZES.
        """
        generate_default_avatar_in_different_sizes(cls)

    @classmethod
    def get_small_avatar_fields(cls) -> list[str]:
        return [f"avatar_small_{key}" for key in cls.AVATAR_SMALL_SIZES.keys()]
