"""
Модуль содержит инфраструктурную логику приложения users.
"""

import os
from typing import TYPE_CHECKING

from users.services.domain import generate_new_filename_with_uuid


if TYPE_CHECKING:
    from ..models import User


def avatar_upload_to(instance: "User", filename: str) -> str:
    return os.path.join("avatars", generate_new_filename_with_uuid(filename))
