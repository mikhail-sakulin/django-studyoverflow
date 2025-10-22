"""
Модуль содержит инфраструктурную логику приложения users.
"""

import os
from dataclasses import astuple, dataclass
from io import BytesIO
from typing import TYPE_CHECKING

from botocore.exceptions import BotoCoreError
from django.core.files.base import ContentFile
from django.core.files.storage import storages
from PIL import Image
from users.services.domain import generate_image, generate_new_filename_with_uuid


if TYPE_CHECKING:
    from ..models import User


storage_default = storages["default"]


def avatar_upload_to(instance: "User", filename: str) -> str:
    return f"avatars/{generate_new_filename_with_uuid(filename)}"


def generate_avatar_small(user: "User") -> bool | str:
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

    # Генерация avatar_small только если avatar доступен
    try:
        # Получение расширения и пути к avatar в хранилище
        root, ext = get_storage_path_to_avatar_with_ext(user)

        # Создание пути к avatar_small
        storage_path_to_avatar_small = f"{root}_small{ext}"

        # Если актуальный avatar_small уже существует, то дубликат не создается
        if not storage_default.exists(storage_path_to_avatar_small):
            # Если нужный avatar_small не создан, то создается avatar_small в BytesIO
            with Image.open(user.avatar) as img:
                buffer = generate_image(img, ext)

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
class OldAvatarNames:
    """
    Dataclass для хранения имен старых файлов аватарок пользователя,
    подлежащих удалению.
    """

    old_avatar_name: None | str = None
    old_avatar_small_name: None | str = None

    def __iter__(self):
        """
        Возвращает итератор по значениям атрибутов в порядке объявления.
        """
        return iter(astuple(self))


def get_old_avatar_names(user: "User") -> OldAvatarNames:
    """
    Получает старые пути в хранилище для avatar и avatar_small для пользователя
    для их последующего удаления.
    """
    old_avatar_names = OldAvatarNames()

    if user.pk:
        old_user = type(user).objects.get(pk=user.pk)
        if old_user.avatar and old_user.avatar.name != user.avatar.name:
            old_avatar_names.old_avatar_name = old_user.avatar.name
        if old_user.avatar_small:
            old_avatar_names.old_avatar_small_name = old_user.avatar_small.name

    return old_avatar_names


def delete_old_avatar_names(old_avatar_names: OldAvatarNames) -> None:
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
