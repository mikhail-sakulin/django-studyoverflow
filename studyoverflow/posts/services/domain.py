"""
Модуль содержит бизнес-логику приложения posts.
"""

from django.utils.text import slugify

from .utils import translit_rus_to_eng


def generate_slug(title: str, max_length: int = 255) -> str:
    """
    Генерирует человекочитаемый slug на основе заголовка.

    Пример:
        generate_slug("Новый заголовок") -> 'novyjj-zagolovok'
    """
    if not isinstance(title, str):
        raise TypeError
    base_slug = slugify(translit_rus_to_eng(title))
    slug = base_slug[:max_length]
    return slug
