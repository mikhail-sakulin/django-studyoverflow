"""
Модуль содержит бизнес-логику приложения users.
"""

import os
import uuid
from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy
from PIL import ImageSequence
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
    """
    Генерирует уникальное имя файла на основе UUID,
    сохраняет исходное расширение, если оно есть.
    """
    root, ext = os.path.splitext(filename)
    ext = ext.lower()
    new_filename = f"{uuid.uuid4().hex}{ext}"
    return new_filename


def generate_image(img: PILImage, ext: str, size: tuple[float, float]) -> BytesIO:
    """
    Создает изображение в BytesIO из PILImage.
    Обрабатывает GIF и статические изображения.
    """
    # Определение формата изображения
    if img.format:
        fmt = img.format
    elif ext:
        fmt = ext.replace(".", "").upper()
    else:
        fmt = "PNG"

    fmt = fmt.replace("JPG", "JPEG")

    # Буфер в памяти
    buffer = BytesIO()

    # --- Обработка анимированного GIF ---
    if fmt == "GIF" and getattr(img, "is_animated", False):
        # Создание GIF в BytesIO
        generate_gif(img, buffer, size)

    # --- Обработка обычных изображений ---
    else:
        # Создание image в BytesIO
        generate_static_image(img, fmt, buffer, size)

    return buffer


def generate_gif(img: PILImage, buffer: BytesIO, size: tuple[float, float]) -> None:
    """
    Генерация уменьшенной анимированной GIF в BytesIO.
    """
    frames = []
    durations = []

    # Ограничение количества кадров для GIF
    max_frames = 100
    for i, frame in enumerate(ImageSequence.Iterator(img)):
        if i >= max_frames:
            break
        frame = frame.convert("RGBA")

        # Уменьшение размера кадра
        frame.thumbnail(size)

        frames.append(frame)
        durations.append(frame.info.get("duration", 100))

    # Если у GIF нет кадров, то ничего не сохраняется
    if not frames:
        return

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

    # Сохранение GIF в buffer
    first_frame.save(buffer, **save_kwargs)


def generate_static_image(
    img: PILImage, fmt: str, buffer: BytesIO, size: tuple[float, float]
) -> None:
    """
    Генерация уменьшенного статического изображения в BytesIO.
    """
    # Если есть альфа-канал, сохранение в RGBA, иначе RGB
    if img.mode in ("RGBA", "LA"):
        img = img.convert("RGBA")
    else:
        img = img.convert("RGB")

    # Уменьшение размера изображения
    img.thumbnail(size)

    # Настройки сохранения
    save_kwargs = {}

    if fmt.upper() in ("JPEG", "WEBP"):
        save_kwargs["quality"] = 100

    # Для PNG/WebP оптимизация
    if fmt.upper() in ("PNG", "WEBP"):
        save_kwargs["optimize"] = True

    # Сохранение картинки в buffer
    img.save(buffer, format=fmt, **save_kwargs)
