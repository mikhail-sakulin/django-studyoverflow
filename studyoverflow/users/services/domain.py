"""
Модуль содержит бизнес-логику приложения users.
"""

import uuid


def generate_new_filename_with_uuid(filename: str) -> str:
    ext = filename.split(".")[-1]
    filename = f"{uuid.uuid4().hex}.{ext}"
    return filename
