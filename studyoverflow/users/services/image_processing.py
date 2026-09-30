"""
Утилиты для обработки изображений приложения users.
"""

from io import BytesIO

from PIL import ImageSequence
from PIL.Image import Image as PILImage


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
