"""
Модуль содержит бизнес-логику приложения users.
"""

import uuid

from django.core.validators import RegexValidator
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy


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


def generate_new_filename_with_uuid(filename: str) -> str:
    ext = filename.split(".")[-1]
    filename = f"{uuid.uuid4().hex}.{ext}"
    return filename
