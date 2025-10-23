"""
Модуль содержит инфраструктурную логику приложения users.
"""

import os
from dataclasses import astuple, dataclass
from io import BytesIO
from typing import TYPE_CHECKING, Type

from botocore.exceptions import BotoCoreError
from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.files.storage import storages
from django.core.validators import RegexValidator
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy
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
class OldAvatarNames:
    """
    Dataclass для хранения имен старых файлов аватарок пользователя,
    подлежащих удалению.
    """

    old_avatar_name: None | str = None
    old_avatar_small_size1_name: None | str = None
    old_avatar_small_size2_name: None | str = None

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
        if old_user.avatar_small_size1:
            old_avatar_names.old_avatar_small_size1_name = old_user.avatar_small_size1.name
        if old_user.avatar_small_size2:
            old_avatar_names.old_avatar_small_size2_name = old_user.avatar_small_size2.name

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


def generate_default_avatar_in_different_sizes(user_model: Type["User"]) -> None:
    """
    Генерирует уменьшенные версии default_avatar всех размеров.
    Используется для создания стандартных аватарок в хранилище.
    """
    # Если default_avatar не существует в хранилище, ничего не создается
    if not storage_default.exists(user_model.DEFAULT_AVATAR_FILENAME):
        return

    # Создание avatar_small уменьшенных размеров
    with storage_default.open(user_model.DEFAULT_AVATAR_FILENAME, "rb") as default_avatar:
        default_avatar.seek(0)
        generate_default_avatar_small(
            user_model, default_avatar, user_model.DEFAULT_AVATAR_SMALL_SIZE1_FILENAME, size_type=1
        )

        default_avatar.seek(0)
        generate_default_avatar_small(
            user_model, default_avatar, user_model.DEFAULT_AVATAR_SMALL_SIZE2_FILENAME, size_type=2
        )


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
