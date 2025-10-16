"""
Модуль содержит инфраструктурную логику приложения users.
"""

import os
from typing import TYPE_CHECKING

from users.services.domain import generate_image, generate_new_filename_with_uuid

from studyoverflow import settings


if TYPE_CHECKING:
    from ..models import User


def avatar_upload_to(instance: "User", filename: str) -> str:
    return os.path.join("avatars", generate_new_filename_with_uuid(filename))


def generate_avatar_small(user: "User") -> bool | str:
    # Если нет avatar, то avatar_small не создается
    if not getattr(user, "avatar", None) or not user.avatar.name:
        return False

    # Если avatar - стандартный (пользователь не задал свой), то avatar_small не создается
    if os.path.basename(user.avatar.name) == "default_avatar.jpg":
        return False

    # Генерация avatar_small только если avatar доступен
    try:
        # Получение полного пути к avatar, имени файла и расширения
        path_to_avatar, root, ext = get_path_to_avatar(user)

        # Создание пути к avatar_small
        path_to_avatar_small = f"{root}_small{ext}"

        # Если avatar_small уже существует, то новый не создается
        if not os.path.exists(path_to_avatar_small):
            # Если avatar_small не существует, то создается изображение
            generate_image(path_to_avatar, ext, path_to_avatar_small)

    except OSError:
        return False

    # Относительный путь до avatar_small, начиная после MEDIA_ROOT
    name_avatar_small = os.path.relpath(path_to_avatar_small, settings.MEDIA_ROOT)

    return name_avatar_small


def get_path_to_avatar(user: "User") -> tuple[str, str, str]:
    # Полный путь до avatar
    path_to_avatar = user.avatar.path

    # Проверка, существует ли файл для avatar
    if not os.path.exists(path_to_avatar):
        raise IOError(f"Путь к аватарке {path_to_avatar} не найден.")

    # Создание полного пути к avatar_small, имя файла на основании
    # имени avatar + "_small".
    root, ext = os.path.splitext(path_to_avatar)

    return path_to_avatar, root, ext


def get_old_avatar_paths(user: "User") -> tuple[str | None, ...]:
    old_avatar_path = None
    old_avatar_small_path = None

    if user.pk:
        old = type(user).objects.get(pk=user.pk)
        if old.avatar and old.avatar.name != user.avatar.name:
            old_avatar_path = old.avatar.path
        if old.avatar_small:
            old_avatar_small_path = old.avatar_small.path

    return old_avatar_path, old_avatar_small_path
