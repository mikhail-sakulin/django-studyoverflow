import logging
import os
from io import BytesIO
from typing import TYPE_CHECKING, Type

from botocore.exceptions import BotoCoreError
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.files.storage import storages
from PIL import Image
from users.services.domain import generate_image, generate_new_filename_with_uuid


if TYPE_CHECKING:
    from users.models import User


logger = logging.getLogger(__name__)


storage_default = storages["default"]


def avatar_upload_to(instance: "User", filename: str) -> str:
    """
    DEPRECATED - используется в старых файлах миграций схемы БД.

    Генерирует путь загрузки основного аватара пользователя в хранилище.

    Возвращает:
        str: avatars/<uuid>.<ext>
    """
    return f"avatars/{generate_new_filename_with_uuid(filename)}"


def user_avatar_upload_path(instance, filename):
    """
    Генерирует путь загрузки основного аватара пользователя в хранилище.

    Если пользователь еще не сохранён (нет pk):
        avatars/tmp/<uuid>.<ext>

    Если пользователь уже существует (есть pk):
        avatars/<user_id>/<uuid>.<ext>
    """
    new_filename = generate_new_filename_with_uuid(filename)

    if instance.pk:
        return f"avatars/{instance.pk}/{new_filename}"

    return f"avatars/tmp/{new_filename}"


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

    except (OSError, ValueError) as e:
        logger.error(
            f"Пользователь: {user.username}: ошибка обработки изображения avatar_small.",
            extra={
                "username": user.username,
                "user_id": user.pk,
                "size_type": size_type,
                "error": str(e),
                "event_type": "avatar_small_processing_error",
            },
        )
        return False

    except BotoCoreError as e:
        logger.error(
            f"Пользователь: {user.username}: ошибка при сохранении avatar_small в хранилище.",
            extra={
                "username": user.username,
                "user_id": user.pk,
                "size_type": size_type,
                "error": str(e),
                "event_type": "avatar_small_storage_error",
            },
        )
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


def get_user_avatar_paths_list(user) -> list[str]:
    """
    Возвращает список путей всех файлов аватаров пользователя, исключая стандартные.
    """
    paths = []
    # Список дефолтных имен, не удаляются из хранилища
    defaults = {
        user.DEFAULT_AVATAR_FILENAME,
        user.DEFAULT_AVATAR_SMALL_SIZE1_FILENAME,
        user.DEFAULT_AVATAR_SMALL_SIZE2_FILENAME,
        user.DEFAULT_AVATAR_SMALL_SIZE3_FILENAME,
    }

    # Проверка основного аватар
    if user.avatar and user.avatar.name not in defaults:
        paths.append(user.avatar.name)

    # Проверка всех миниатюр
    for field_name in user.get_small_avatar_fields():
        field_value = getattr(user, field_name)
        if field_value and field_value.name not in defaults:
            paths.append(field_value.name)

    return paths


def get_old_avatar_names(user: "User") -> tuple[str | None, list[str]]:
    """
    Возвращает путь avatar из БД и список путей файлов аватаров, которые нужно удалить
    при обновлении пользователя.
    """
    if not user.pk:
        return None, []

    old_user = type(user).objects.get(pk=user.pk)
    avatar_name_in_db = old_user.avatar.name

    avatar_names_for_delete = []

    if user.avatar.name != avatar_name_in_db:
        avatar_names_for_delete = get_user_avatar_paths_list(old_user)

    return avatar_name_in_db, avatar_names_for_delete


def delete_old_avatar_names(old_avatar_names: list[str]) -> None:
    """
    Удаляет старые файлы avatar и avatar_small (миниатюры) пользователя из хранилища.
    """
    for name in old_avatar_names:
        if name and storage_default.exists(name):
            try:
                storage_default.delete(name)
            except BotoCoreError as e:
                logger.error(
                    f"Ошибка при удалении файла '{name}' из хранилища.",
                    extra={
                        "file_name": name,
                        "error": str(e),
                        "event_type": "avatar_file_delete_error",
                    },
                )
                pass


def generate_default_avatar_in_different_sizes(user_model: Type["User"]) -> None:
    """
    Генерирует уменьшенные версии стандартного default_avatar
    для всех размеров, указанных в AVATAR_SMALL_SIZES.
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

    except (OSError, ValueError) as e:
        logger.error(
            f"Ошибка обработки изображения default_avatar для размера size{size_type}.",
            extra={
                "size_type": size_type,
                "path": storage_path_to_avatar_small,
                "error": str(e),
                "event_type": "default_avatar_small_processing_error",
            },
        )
        return

    except BotoCoreError as e:
        logger.error(
            "Ошибка при сохранении default_avatar_small в хранилище.",
            extra={
                "size_type": size_type,
                "path": storage_path_to_avatar_small,
                "error": str(e),
                "event_type": "default_avatar_small_storage_error",
            },
        )
        return
