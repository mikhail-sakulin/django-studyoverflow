import filetype
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy
from PIL import Image


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


@deconstructible
class AvatarFileValidator:
    """
    Класс-валидатор для проверки аватаров пользователей.

    Проверяет:
        - размер файла,
        - MIME-тип файла,
        - минимальные размеры изображения,
        - соотношения сторон изображения.
    """

    # Разрешенные MIME-типы файлов
    ALLOWED_MIME_TYPES = (
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "image/x-icon",
    )

    def __init__(self, max_size: int = 10 * 1024 * 1024):
        self.max_size = max_size
        self.min_height = 100
        self.min_width = 100
        self.min_aspect_ration = 0.25
        self.max_aspect_ration = 4

    def __call__(self, file, *args, **kwargs):
        # Проверка размера файла
        if file.size > self.max_size:
            max_size_mb = self.max_size / (1024 * 1024)
            raise ValidationError(
                gettext_lazy(f"Максимальный разрешенный размер файла: {max_size_mb} Mb."),
                code="file_too_large",
            )

        # Проверка MIME-типа файла по содержимому
        try:
            # Получение MIME-типа
            kind = filetype.guess(file.read(1024))
            file.seek(0)
        except Exception:
            # Если magic не смог прочитать файл
            raise ValidationError(gettext_lazy("Не удалось определить тип файла."))

        if not kind or kind.mime not in self.ALLOWED_MIME_TYPES:
            raise ValidationError(
                gettext_lazy(
                    f"Недопустимый тип файла, разрешены только: "
                    f"{', '.join(el.split('/')[-1] for el in self.ALLOWED_MIME_TYPES)}."
                ),
                code="invalid_file_type",
            )

        # Проверка размеров и соотношения сторон
        img = Image.open(file)
        width, height = img.size

        if width < self.min_width or height < self.min_height:
            raise ValidationError(
                gettext_lazy(
                    f"Изображение слишком маленькое. Разрешенный минимум: "
                    f"{self.min_width}x{self.min_height} px."
                ),
                code="file_too_small",
            )

        aspect_ratio = width / height

        if aspect_ratio < self.min_aspect_ration or aspect_ratio > self.max_aspect_ration:
            raise ValidationError(
                gettext_lazy(
                    f"Недопустимое соотношение сторон изображения. Допустимо "
                    f"{self.min_aspect_ration}-{self.max_aspect_ration}."
                ),
                code="invalid_file_aspect_ration",
            )
