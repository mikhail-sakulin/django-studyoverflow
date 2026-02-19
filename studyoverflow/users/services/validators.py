from datetime import date
from typing import Final

import filetype
from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.validators import RegexValidator
from django.utils import timezone
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy
from PIL import Image

from studyoverflow import settings


@deconstructible
class CustomUsernameValidator(RegexValidator):
    """
    Валидатор для username пользователя:
    - минимум 4 символа;
    - разрешены только латинские буквы, цифры, "_" и "-".
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
    Валидатор для first_name и last_name пользователя:
    - разрешены только буквы из Unicode и дефис;
    - запрещены цифры, пробелы и спецсимволы;
    - пустое значение разрешено;
    - не допускается начинать или заканчивать строку дефисом;
    - не допускается несколько подряд идущих дефисов;
    - строка не может состоять только из дефисов.
    """

    message = gettext_lazy("Имя и фамилия должны состоять только из букв, дефис разрешен.")
    code = "invalid_name"

    def __call__(self, value: str):
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
    Валидатор для проверки аватаров пользователей.

    Проверяет:
    - максимальный размер файла;
    - MIME-тип файла;
    - минимальные размеры изображения;
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

    MAX_SIZE: Final = 10 * 1024 * 1024
    MIN_HEIGHT: Final = 100
    MIN_WIDTH: Final = 100
    MIN_ASPECT_RATION: Final = 0.25
    MAX_ASPECT_RATION: Final = 4

    def __call__(self, file: File, *args, **kwargs):
        # Проверка размера файла
        if file.size > self.MAX_SIZE:
            max_size_mb = self.MAX_SIZE / (1024 * 1024)
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

        if width < self.MIN_WIDTH or height < self.MIN_HEIGHT:
            raise ValidationError(
                gettext_lazy(
                    f"Изображение слишком маленькое. Разрешенный минимум: "
                    f"{self.MIN_WIDTH}x{self.MIN_HEIGHT} px."
                ),
                code="file_too_small",
            )

        aspect_ratio = width / height

        if aspect_ratio < self.MIN_ASPECT_RATION or aspect_ratio > self.MAX_ASPECT_RATION:
            raise ValidationError(
                gettext_lazy(
                    f"Недопустимое соотношение сторон изображения. Допустимо "
                    f"{self.MIN_ASPECT_RATION}-{self.MAX_ASPECT_RATION}."
                ),
                code="invalid_file_aspect_ration",
            )


@deconstructible
class BirthDateValidator:
    """
    Валидатор для проверки даты рождения пользователя.

    Проверяет:
    - дата рождения не в будущем;
    - текущий возраст не превышает MAX_AGE лет.
    """

    MAX_AGE: Final = 120

    def __call__(self, value: date):
        today = timezone.localdate()
        if value > today:
            raise ValidationError(
                "Дата рождения не может быть в будущем. "
                f'Указывайте дату с учетом часового пояса "{settings.TIME_ZONE}".',
                code="future_date",
            )

        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))

        if age > self.MAX_AGE:
            raise ValidationError(
                f"Возраст не может превышать {self.MAX_AGE} лет.", code="max_age_exceeded"
            )
