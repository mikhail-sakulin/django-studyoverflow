"""
Модуль содержит бизнес-логику приложения users.
"""

import os
import uuid

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy
from PIL import Image, ImageSequence
from PIL.Image import Image as PILImage


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


def generate_new_filename_with_uuid(filename: str) -> str:
    ext = filename.split(".")[-1]
    filename = f"{uuid.uuid4().hex}.{ext}"
    return filename


def generate_image(path_to_default_image: str, ext: str, path_to_generate_image: str) -> None:
    # Генерация avatar_small, открытие исходного avatar для обработки
    with Image.open(path_to_default_image) as img:

        # Определение формата изображения
        if img.format:
            fmt = img.format
        elif ext:
            fmt = ext.replace(".", "").upper()
        else:
            fmt = "PNG"

        fmt = fmt.replace("JPG", "JPEG")

        # --- Обработка анимированного GIF ---
        if fmt == "GIF" and getattr(img, "is_animated", False):
            generate_gif(img, path_to_generate_image)

        # --- Обработка обычных изображений ---
        else:
            generate_static_image(img, fmt, path_to_generate_image)


def generate_gif(img: PILImage, path_to_generate_image: str) -> None:
    frames = []
    durations = []

    # Ограничение количества кадров
    max_frames = 100
    for i, frame in enumerate(ImageSequence.Iterator(img)):
        if i >= max_frames:
            break
        frame = frame.convert("RGBA")

        # Уменьшение размера кадра
        frame.thumbnail((150, 150))

        frames.append(frame)
        durations.append(frame.info.get("duration", 100))

    # Метаданные первого кадра
    first_frame = frames[0]
    loop = img.info.get("loop", 0)
    disposal = img.info.get("disposal", 2)
    transparency = img.info.get("transparency")

    # Настройки сохранения GIF
    save_kwargs = {
        "save_all": True,
        "append_images": frames[1:],
        "loop": loop,
        "duration": durations,
        "disposal": disposal,
        "format": "GIF",
    }
    if transparency is not None:
        save_kwargs["transparency"] = transparency

    # Сохранение GIF
    first_frame.save(path_to_generate_image, **save_kwargs)


def generate_static_image(img: PILImage, fmt: str, path_to_generate_image: str) -> None:
    # Если есть альфа-канал, сохранение в RGBA, иначе RGB
    if img.mode in ("RGBA", "LA"):
        img = img.convert("RGBA")
    else:
        img = img.convert("RGB")

    # Уменьшение размера изображения
    img.thumbnail((150, 150))

    # Настройки сохранения
    save_kwargs = {}

    if fmt.upper() in ("JPEG", "WEBP"):
        save_kwargs["quality"] = 100

    # Для PNG/WebP оптимизация
    if fmt.upper() in ("PNG", "WEBP"):
        save_kwargs["optimize"] = True

    # Сохранение картинки
    img.save(path_to_generate_image, format=fmt, **save_kwargs)


def delete_old_avatar_paths(old_avatar_paths: tuple[str | None, ...]) -> None:
    for path in old_avatar_paths:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass
