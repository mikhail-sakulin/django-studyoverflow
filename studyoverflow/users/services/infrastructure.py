"""
Модуль содержит инфраструктурную логику приложения users.
"""

import os
from dataclasses import astuple, dataclass
from io import BytesIO
from typing import TYPE_CHECKING, Type

import filetype
from botocore.exceptions import BotoCoreError
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.files.storage import storages
from django.core.validators import RegexValidator
from django.db.models import F
from django.db.models.functions import Greatest
from django.http import HttpRequest
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy
from django_redis import get_redis_connection
from PIL import Image
from users.services.domain import generate_image, generate_new_filename_with_uuid


if TYPE_CHECKING:
    from ..models import User


storage_default = storages["default"]


def avatar_upload_to(instance: "User", filename: str) -> str:
    return f"avatars/{generate_new_filename_with_uuid(filename)}"


@deconstructible
class CustomUsernameValidator(RegexValidator):
    """
    Класс-валидатор для username:
        - минимум 4 символа,
        - разрешены только латинские буквы, цифры, _ и -.
    """

    regex = r"^[a-zA-Z0-9_-]{4,}$"
    message = gettext_lazy(
        "Имя пользователя должно быть не менее 4 символов и "
        "состоять только из латинских букв, цифр, символов _ и -."
    )
    flags = 0


@deconstructible
class PersonalNameValidator:
    """
    Класс-валидатор для first_name и last_name:
        - разрешены только буквы из Unicode и дефис,
        - запрещены цифры, пробелы и спецсимволы.
    """

    message = gettext_lazy("Имя и фамилия должны состоять только из букв, дефис разрешен.")
    code = "invalid_name"

    def __call__(self, value):
        # Пустое значение разрешено
        if not value:
            return

        # Проверка отсутствия пробелов (отдельная для сообщения)
        if " " in value:
            raise ValidationError(
                gettext_lazy("Имя и фамилия не должны содержать пробелы."), code=self.code
            )

        # Проверка, что все символы являются или буквами, или дефисами
        if not all(char.isalpha() or char == "-" for char in value):
            raise ValidationError(self.message, code=self.code)

        # Все символы не могут быть только дефисами
        if all(char == "-" for char in value):
            raise ValidationError(
                gettext_lazy("Имя и фамилия не могут состоять только из дефисов."), code=self.code
            )

        # Строка не должна начинаться или заканчиваться на дефис
        if value[0] == "-" or value[-1] == "-":
            raise ValidationError(
                gettext_lazy("Имя и фамилия не должны начинаться или заканчиваться на дефис."),
                code=self.code,
            )

        # Два дефиса не могут идти подряд
        if "--" in value:
            raise ValidationError(
                gettext_lazy("Имя и фамилия не должны содержать подряд несколько дефисов."),
                code=self.code,
            )


@deconstructible
class AvatarFileValidator:
    """
    Класс-валидатор для проверки аватаров пользователей.

    Проверяет:
        - размер файла,
        - MIME-тип файла,
        - минимальные размеры изображения,
        - соотношения сторон изображения.
    """

    # Разрешенные MIME-типы файлов
    ALLOWED_MIME_TYPES = (
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "image/x-icon",
    )

    def __init__(self, max_size: int = 10 * 1024 * 1024):
        self.max_size = max_size
        self.min_height = 200
        self.min_width = 200
        self.min_aspect_ration = 0.25
        self.max_aspect_ration = 4

    def __call__(self, file, *args, **kwargs):
        # Проверка размера файла
        if file.size > self.max_size:
            max_size_mb = self.max_size / (1024 * 1024)
            raise ValidationError(
                gettext_lazy(f"Максимальный разрешенный размер файла: {max_size_mb} Mb."),
                code="file_too_large",
            )

        # Проверка MIME-типа файла по содержимому
        try:
            # Получение MIME-типа
            kind = filetype.guess(file.read(1024))
            file.seek(0)
        except Exception:
            # Если magic не смог прочитать файл
            raise ValidationError(gettext_lazy("Не удалось определить тип файла."))

        if not kind or kind.mime not in self.ALLOWED_MIME_TYPES:
            raise ValidationError(
                gettext_lazy(
                    f"Недопустимый тип файла, разрешены только: "
                    f"{', '.join(el.split('/')[-1] for el in self.ALLOWED_MIME_TYPES)}."
                ),
                code="invalid_file_type",
            )

        # Проверка размеров и соотношения сторон
        img = Image.open(file)
        width, height = img.size

        if width < self.min_width or height < self.min_height:
            raise ValidationError(
                gettext_lazy(
                    f"Изображение слишком маленькое. Разрешенный минимум: "
                    f"{self.min_width}x{self.min_height} px."
                ),
                code="file_too_small",
            )

        aspect_ratio = width / height

        if aspect_ratio < self.min_aspect_ration or aspect_ratio > self.max_aspect_ration:
            raise ValidationError(
                gettext_lazy(
                    f"Недопустимое соотношение сторон изображения. Допустимо "
                    f"{self.min_aspect_ration}-{self.max_aspect_ration}."
                ),
                code="invalid_file_aspect_ration",
            )


def update_user_counter_field(author_id: int, counter_field: str, value_change: int):
    author_model = get_user_model()

    if not hasattr(author_model, counter_field):
        raise ValueError(f"User has no field {counter_field}")

    author_model.objects.filter(pk=author_id).update(
        **{counter_field: Greatest(F(counter_field) + value_change, 0)}
    )


def generate_avatar_small(user: "User", size_type: int) -> bool | str:
    """
    Генерирует уменьшенную версию avatar пользователя.
    Возвращает путь avatar_small в хранилище или False, если avatar_small не создается.
    """
    # Если нет avatar, то avatar_small не создается
    if not getattr(user, "avatar", None) or not user.avatar.name:
        return False

    # Если avatar - стандартный (пользователь не задал свой), то avatar_small не создается
    if os.path.basename(user.avatar.name) == "default_avatar.jpg":
        return False

    # Если передан некорректный size_type, то avatar_small не создается
    if f"size{size_type}" not in user.AVATAR_SMALL_SIZES:
        return False

    # Генерация avatar_small только если avatar доступен
    try:
        # Получение расширения и пути к avatar в хранилище
        root, ext = get_storage_path_to_avatar_with_ext(user)

        # Создание пути к avatar_small
        storage_path_to_avatar_small = f"{root}_small_size{size_type}{ext}"

        # Если актуальный avatar_small уже существует, то дубликат не создается
        if not storage_default.exists(storage_path_to_avatar_small):
            # Если нужный avatar_small не создан, то создается avatar_small в BytesIO
            with Image.open(user.avatar) as img:
                buffer = generate_image(img, ext, user.AVATAR_SMALL_SIZES[f"size{size_type}"])

            # Сохранение avatar_small (из BytesIO) в хранилище
            save_img_in_storage(buffer, storage_path_to_avatar_small)

    except (OSError, ValueError):
        # Ошибка обработки изображения
        return False

    except BotoCoreError:
        # Ошибка при обращении к хранилищу
        return False

    # Путь к avatar_small в хранилище
    return storage_path_to_avatar_small


def get_storage_path_to_avatar_with_ext(user: "User") -> tuple[str, str]:
    """
    Возвращает кортеж (путь без расширения, расширение файла) для avatar пользователя.
    """
    # Путь к avatar в хранилище и его расширение
    root, ext = os.path.splitext(user.avatar.name)
    return root, ext


def save_img_in_storage(buffer: BytesIO, storage_path_to_avatar_small: str) -> None:
    """
    Сохраняет изображение из BytesIO в хранилище.
    """
    buffer.seek(0)
    storage_default.save(storage_path_to_avatar_small, ContentFile(buffer.read()))


@dataclass(slots=True)
class AvatarNamesForDelete:
    """
    Dataclass для хранения имен старых файлов аватарок пользователя,
    подлежащих удалению.
    """

    old_avatar_name: None | str = None
    old_avatar_small_size1_name: None | str = None
    old_avatar_small_size2_name: None | str = None
    old_avatar_small_size3_name: None | str = None

    def __iter__(self):
        """
        Возвращает итератор по значениям атрибутов в порядке объявления.
        """
        return iter(astuple(self))


def get_old_avatar_names(user: "User") -> tuple[str | None, AvatarNamesForDelete]:
    """
    Получает старые пути в хранилище для avatar и avatar_small для пользователя
    для их последующего удаления.
    """
    avatar_names_for_delete = AvatarNamesForDelete()
    avatar_name_in_db = None

    if user.pk:
        old_user = type(user).objects.get(pk=user.pk)
        avatar_name_in_db = old_user.avatar.name

        if (
            old_user.avatar
            and old_user.avatar != user._meta.get_field("avatar").get_default()
            and old_user.avatar.name != user.avatar.name
        ):
            avatar_names_for_delete.old_avatar_name = old_user.avatar.name
        else:
            return avatar_name_in_db, avatar_names_for_delete

        for avatar_small in user.get_small_avatar_fields():
            avatar_small_field = getattr(old_user, avatar_small)

            if (
                avatar_small_field
                and avatar_small_field != user._meta.get_field(avatar_small).get_default()
            ):
                setattr(
                    avatar_names_for_delete, f"old_{avatar_small}_name", avatar_small_field.name
                )

    return avatar_name_in_db, avatar_names_for_delete


def delete_old_avatar_names(old_avatar_names: AvatarNamesForDelete | list[str]) -> None:
    """
    Удаляет старые файлы для avatar и avatar_small пользователя из хранилища.
    """
    for name in old_avatar_names:
        if name and storage_default.exists(name):
            try:
                storage_default.delete(name)
            except BotoCoreError:
                # Ошибка при обращении к хранилищу
                pass


def generate_default_avatar_in_different_sizes(user_model: Type["User"]) -> None:
    """
    Генерирует уменьшенные версии default_avatar всех размеров.
    Используется для создания стандартных аватарок в хранилище.
    """
    # Если default_avatar не существует в хранилище, ничего не создается
    if not storage_default.exists(user_model.DEFAULT_AVATAR_FILENAME):
        return

    with storage_default.open(user_model.DEFAULT_AVATAR_FILENAME, "rb") as default_avatar:
        for size_type, filename in (
            (1, user_model.DEFAULT_AVATAR_SMALL_SIZE1_FILENAME),
            (2, user_model.DEFAULT_AVATAR_SMALL_SIZE2_FILENAME),
            (3, user_model.DEFAULT_AVATAR_SMALL_SIZE3_FILENAME),
        ):
            generate_default_avatar_small(user_model, default_avatar, filename, size_type)
            default_avatar.seek(0)


def generate_default_avatar_small(
    user_model: Type["User"],
    default_avatar: File,
    storage_path_to_avatar_small: str,
    size_type: int,
) -> None:
    """
    Генерирует уменьшенную версию default_avatar для одного размера.
    Сохраняет avatar_small в хранилище по указанному пути.
    """
    try:
        root, ext = os.path.splitext(storage_path_to_avatar_small)

        # Если нужный avatar_small не создан, то создается avatar_small в BytesIO
        with Image.open(default_avatar) as img:
            buffer = generate_image(img, ext, user_model.AVATAR_SMALL_SIZES[f"size{size_type}"])

        # Сохранение avatar_small (из BytesIO) в хранилище
        save_img_in_storage(buffer, storage_path_to_avatar_small)

    except (OSError, ValueError):
        # Ошибка обработки изображения
        return

    except BotoCoreError:
        # Ошибка при обращении к хранилищу
        return


REDIS_KEY_PREFIX = "online_user"
ONLINE_TTL = 120


def get_redis_conn_with_key(user_id: int):
    """
    Возвращает объект-соединение с Redis и ключ в Redis для статуса онлайна пользователя.
    """
    redis_conn = get_redis_connection("default")
    key = f"{REDIS_KEY_PREFIX}:{user_id}"
    return redis_conn, key


def set_user_online(user_id: int):
    """
    Установка ключа в Redis с TTL, что пользователь онлайн.
    """
    redis_conn, key = get_redis_conn_with_key(user_id)
    redis_conn.set(key, "1", ex=ONLINE_TTL)


def is_user_online(user_id: int) -> bool:
    """
    Проверка, что пользователь онлайн.
    """
    redis_conn, key = get_redis_conn_with_key(user_id)
    return redis_conn.exists(key) == 1


def get_online_user_ids():
    redis_conn = get_redis_connection("default")
    keys = redis_conn.keys("online_user:*")

    return [int(key.decode().split(":")[1]) for key in keys]


class UserOnlineFilterMixin:
    request: HttpRequest

    online_param = "online"

    def filter_by_online(self, queryset):
        online = self.request.GET.get(self.online_param, "any")

        if online == "any":
            return queryset

        self.online_ids = get_online_user_ids()

        if online == "online":
            return queryset.filter(id__in=self.online_ids)

        return queryset.exclude(id__in=self.online_ids)

    def get_online_ids(self):
        return getattr(self, "online_ids", get_online_user_ids())


class UserSortMixin:
    request: HttpRequest

    sort_param = "user_sort"
    order_param = "user_order"

    sort_map = {
        "name": "username",
        "reputation": "reputation",
        "posts": "posts_count",
        "comments": "comments_count",
    }

    default_sort = "reputation"
    default_order = "desc"

    def apply_sorting(self, queryset):
        sort = self.request.GET.get(self.sort_param, self.default_sort)
        order = self.request.GET.get(self.order_param, self.default_order)

        sort = sort if sort in self.sort_map else self.default_sort
        order = order if order in ("asc", "desc") else self.default_order

        field = self.sort_map[sort]
        if order == "desc":
            field = f"-{field}"

        return queryset.order_by(field, "username")


class UserHTMXPaginationMixin:
    request: HttpRequest

    paginate_htmx_by = 9
    offset_param = "offset"
    limit_param = "limit"

    def paginate_queryset(self, queryset):
        offset = self.request.GET.get(self.offset_param, 0)
        limit = self.request.GET.get(self.limit_param, self.paginate_htmx_by)

        try:
            offset = int(offset)
            limit = int(limit)
        except ValueError:
            return queryset.none()

        self.offset = offset
        self.limit = limit

        if limit > 0:
            self.remaining = queryset[offset + limit : offset + limit + 1].exists()
            return queryset[offset : offset + limit]

        self.remaining = False
        return queryset[offset:]
