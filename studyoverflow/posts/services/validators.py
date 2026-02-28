from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

from .text_processing import normalize_tag_name


if TYPE_CHECKING:
    from posts.models import Comment


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


def validate_comment(  # noqa: C901 (is too complex)
    content: str,
    parent_comment: Optional[Comment],
    reply_to: Optional[Comment],
    post_id: int,
    instance_pk: Optional[int] = None,
) -> dict[str, str]:
    """
    Валидатор иерархии и целостности комментариев.

    Проверяет:
    - Наличие текста в комментарии.
    - Синхронизацию parent_comment и reply_to (должны присутствовать оба для ответов).
    - Отсутствие ссылок комментария на самого себя.
    - Принадлежность parent_comment и reply_to к указанному посту.
    - Корректность вложенности (reply_to должен быть частью ветки parent_comment).
    """
    errors = {}

    # Проверка содержимого комментария (контента)
    if not content or not content.strip():
        errors["content"] = "Комментарий не может быть пустым."

    # Проверка, что одновременно указаны parent и reply
    if parent_comment and not reply_to:
        errors["reply_to"] = "Для дочернего комментария необходимо указать reply_to."

    if reply_to and not parent_comment:
        errors["parent_comment"] = "Для ответа необходимо указать parent_comment."

    # Валидация указанного родительского комментария
    if parent_comment:
        if instance_pk and parent_comment.pk == instance_pk:
            errors["parent_comment"] = "Комментарий не может быть родителем сам себе."

        if post_id and parent_comment.post_id != post_id:
            errors["parent_comment"] = "Родительский комментарий принадлежит другому посту."

    # Валидация указанного комментария, к которому создается ответ (текущий комментарий)
    if reply_to:
        if instance_pk and reply_to.pk == instance_pk:
            errors["reply_to"] = "Комментарий не может отвечать сам себе."

        if post_id and reply_to.post_id != post_id:
            errors["reply_to"] = "Комментарий для ответа принадлежит другому посту."

        # Проверка иерархии веток
        if parent_comment:
            # Если у reply_to другой родитель
            if reply_to.parent_comment_id and reply_to.parent_comment_id != parent_comment.pk:
                errors["reply_to"] = "Неверный комментарий для ответа (другая ветка)."

            # Если ответ создается к parent_comment, то проверка, что reply_to == parent_comment
            elif not reply_to.parent_comment_id and reply_to.pk != parent_comment.pk:
                errors["reply_to"] = "Ответ должен ссылаться на корень ветки или его детей."

    return errors
