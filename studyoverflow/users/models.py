from celery import chain
from django.contrib.auth.models import AbstractUser, Group, UserManager
from django.core.validators import MaxLengthValidator
from django.db import models, transaction
from django.db.models import Q
from django.db.models.functions import Upper
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy
from users.services import (
    AvatarFileValidator,
    CustomUsernameValidator,
    PersonalNameValidator,
    generate_default_avatar_in_different_sizes,
    get_old_avatar_names,
    user_avatar_upload_path,
)


class CustomUserManager(UserManager):
    """
    Кастомный менеджер пользователей.

    Позволяет искать пользователя как по username, так и по email.
    """

    def get_by_natural_key(self, username_or_email):
        """Возвращает пользователя по username или email."""
        return self.get(Q(username=username_or_email) | Q(email__iexact=username_or_email))


class User(AbstractUser):
    """
    Кастомная модель пользователя (наследование от django.contrib.auth.models.AbstractUser).

    Поля (без учета наследования):
    - username (CharField): Уникальное имя пользователя.
    - email (EmailField): Уникальный email.
    - first_name (CharField): Имя.
    - last_name (CharField): Фамилия.
    - bio (TextField): Информация о пользователе.
    - date_birth (DateField): Дата рождения.
    - avatar (ImageField): Основной аватар.
    - avatar_small_size1 (ImageField): Миниатюра аватара №1 (100x100).
    - avatar_small_size2 (ImageField): Миниатюра аватара №2 (170x170).
    - avatar_small_size3 (ImageField): Миниатюра аватара №3 (800x800).
    - reputation (IntegerField): Репутация пользователя.
    - posts_count (PositiveIntegerField): Количество постов.
    - comments_count (PositiveIntegerField): Количество комментариев.
    - date_joined (DateTimeField): Время создания аккаунта.
    - last_seen (DateTimeField): Последняя активность пользователя.
    - is_social (BooleanField): Флаг регистрации через соцсети.
    - role (CharField): Роль пользователя.
    - is_blocked (BooleanField): Флаг блокировки.
    - blocked_at (DateTimeField): Дата и время блокировки.
    - blocked_by (ForeignKey): Пользователь, заблокировавший аккаунт.

    Прописана логика:
    - синхронизация роли пользователя с флагами is_staff / is_superuser;
    - синхронизация роли пользователя с группами Django;
    - обработка загрузки, удаления и обновления аватара;
    - асинхронные генерация миниатюр аватара и удаление старых файлов через Celery.
    """

    class Role(models.TextChoices):
        """
        Перечисление ролей пользователей.
        """

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

    # Соответствие ролей пользователей и флагов "is_staff" и "is_superuser"
    ROLE_FLAGS_MAP = {
        Role.ADMIN: {"is_staff": True, "is_superuser": True},
        Role.MODERATOR: {"is_staff": True, "is_superuser": False},
        Role.STAFF_VIEWER: {"is_staff": True, "is_superuser": False},
        Role.USER: {"is_staff": False, "is_superuser": False},
    }
    # Соответствие ролей пользователей и групп прав
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
        max_length=30,
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
        max_length=50, blank=True, validators=[first_name_last_name_validator], verbose_name="Имя"
    )
    last_name = models.CharField(
        max_length=50,
        blank=True,
        validators=[first_name_last_name_validator],
        verbose_name="Фамилия",
    )
    bio = models.TextField(
        blank=True,
        max_length=300,
        validators=[MaxLengthValidator(300)],
        verbose_name="Информация о пользователе",
    )
    date_birth = models.DateField(blank=True, null=True, verbose_name="Дата рождения")

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

    reputation = models.IntegerField(default=0, verbose_name="Репутация")
    posts_count = models.PositiveIntegerField(default=0, verbose_name="Количество постов")
    comments_count = models.PositiveIntegerField(default=0, verbose_name="Количество комментариев")

    date_joined = models.DateTimeField(auto_now_add=True, verbose_name="Время создания аккаунта")
    last_seen = models.DateTimeField(
        default=timezone.now,
        verbose_name="Был в сети",
    )

    is_social = models.BooleanField(default=False, verbose_name="Через соцсеть")
    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.USER, verbose_name="Роль"
    )

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

    objects = CustomUserManager()

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["username"]
        permissions = [
            ("block_user", "Can block/unblock users"),
        ]
        indexes = [
            # Индекс для поиска пользователя по имени без учета регистра:
            #   queryset.filter(author__username__iexact=author)
            #       WHERE UPPER(username) = UPPER(?)
            models.Index(Upper("username"), name="user_username_upper_idx"),
            # Индекс для сортировки пользователей по последнему визиту:
            #   User.objects.order_by('last_seen')
            #       ORDER BY last_seen DESC
            models.Index(fields=["last_seen"]),
            # Индекс для сортировки пользователей по репутации по убыванию и имени по возрастанию:
            #   User.objects.order_by('-reputation', 'username')
            models.Index(fields=["-reputation", "username"]),
            # Индекс для сортировки пользователей по количеству постов по убыванию
            # и имени по возрастанию:
            #   User.objects.order_by('-posts_count', 'username')
            models.Index(fields=["-posts_count", "username"]),
            # Индекс для сортировки пользователей по количеству комментариев по убыванию
            # и имени по возрастанию:
            #   User.objects.order_by('-comments_count', 'username')
            models.Index(fields=["-comments_count", "username"]),
        ]

    def __str__(self):
        """Возвращает строковое представление пользователя."""
        return self.username

    def save(self, *args, **kwargs):
        """
        Добавлена логика при сохранении пользователя:
        - синхронизация роли и флагов "is_staff" и "is_superuser";
        - синхронизация роли с группами Django;
        - обработка загрузки, удаления и изменения аватара;
        - отложенный запуск Celery-задач после подтверждения транзакции БД
          для генерации миниатюр аватара и удаление старых файлов.
        """
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

    def get_absolute_url(self):
        """Возвращает уникальный URL профиля пользователя."""
        return reverse("users:profile", kwargs={"username": self.username})

    def get_avatar_small_url(self, size="size1"):
        """
        Возвращает URL конкретной миниатюры или URL оригинала аватара.
        """
        fields = {
            "size1": self.avatar_small_size1,
            "size2": self.avatar_small_size2,
            "size3": self.avatar_small_size3,
        }
        target_field = fields.get(size)
        if target_field:
            return target_field.url
        return self.avatar.url if self.avatar else None

    @property
    def avatar_small_size1_url(self):
        """URL миниатюры аватара размера size1."""
        return self.get_avatar_small_url("size1")

    @property
    def avatar_small_size2_url(self):
        """URL миниатюры аватара размера size2."""
        return self.get_avatar_small_url("size2")

    @property
    def avatar_small_size3_url(self):
        """URL миниатюры аватара размера size3."""
        return self.get_avatar_small_url("size3")

    def _sync_role_flags(self):
        """
        Синхронизирует флаги "is_staff" и "is_superuser" и роль.

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
        Назначает или удаляет группы "Moderators" и "StaffViewers" в зависимости от роли.
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
        is_new_upload = not is_deleted and self.avatar.name != avatar_name_in_db

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
        """
        Сбрасывает значения миниатюр аватара.

        Если default=True — устанавливает стандартные значения, иначе очищает поля.
        """
        for field_name in self.get_small_avatar_fields():
            if default:
                value = self._meta.get_field(field_name).get_default()
            else:
                value = None
            setattr(self, field_name, value)

    def _schedule_creation_celery_tasks(self):
        """
        Задачи Celery при создании пользователя.

        Генерирует миниатюры аватара, если используется не стандартный аватар.
        """
        from users.tasks import generate_and_save_avatars_small

        default_avatar = self._meta.get_field("avatar").get_default()
        if self.avatar != default_avatar:
            transaction.on_commit(lambda: generate_and_save_avatars_small.delay(self.pk))

    def _schedule_update_celery_tasks(self, context: dict):
        """
        Задачи Celery при обновлении пользователя.

        Обрабатывает:
        - генерацию миниатюр;
        - удаление старых файлов из S3-хранилища.
        """
        from users.tasks import delete_old_avatars_from_s3_storage, generate_and_save_avatars_small

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
                delete_old_avatars_from_s3_storage.si(self.pk, avatar_names_for_delete),
            )

            # Запуск задач только после завершения сохранения в БД
            transaction.on_commit(lambda: tasks.apply_async())

        elif is_deleted and not was_default:
            # celery задача на удаление после завершения сохранения в БД
            transaction.on_commit(
                lambda: delete_old_avatars_from_s3_storage.delay(self.pk, avatar_names_for_delete)
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
        """Возвращает список имен полей миниатюр аватара."""
        return [f"avatar_small_{key}" for key in cls.AVATAR_SMALL_SIZES.keys()]
