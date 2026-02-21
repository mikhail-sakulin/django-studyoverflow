from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

from .text_processing import normalize_tag_name


@deconstructible
class PostTitleValidator:
    """
    Валидатор для проверки заголовка поста.

    Проверяет:
    - минимальную длину заголовка;
    - максимальную длину заголовка.
    """

    def __init__(self, min_len=10, max_len=255):
        self.min_len = min_len
        self.max_len = max_len

    def __call__(self, title):
        if len(title) < self.min_len:
            raise ValidationError(
                f"Длина заголовка должна быть не менее {self.min_len} символов.",
                code="title_too_short",
            )

        if len(title) > self.max_len:
            raise ValidationError(
                f"Длина заголовка должна быть не более {self.max_len} символов.",
                code="title_too_long",
            )


def validate_and_normalize_tags(tags_list: list[str]) -> list[str]:
    """
    Валидатор для проверки количества тегов в списке, их длины и их нормализации.

    Проверяет:
    - минимальное количество тегов;
    - максимальное количество тегов.

    Приводит имя тега к нормальному виду.
    Если длина имени тега превышает максимальное значение, вызывает исключение.
    """

    if not tags_list:
        raise ValidationError("Укажите хотя бы 1 тег.", code="too_few_tags")

    if len(tags_list) > 10:
        raise ValidationError("Укажите не более 10 тегов.", code="too_many_tags")

    normalized_tags = []

    max_tag_name_length = 50

    for tag in tags_list:
        normalized_tag_name = normalize_tag_name(tag)

        if len(normalized_tag_name) > max_tag_name_length:
            raise ValidationError(f"Длина тега не может превышать {max_tag_name_length} символов.")

        normalized_tags.append(normalized_tag_name)

    return normalized_tags
