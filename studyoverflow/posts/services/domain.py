"""
Модуль содержит бизнес-логику приложения posts.
"""

import bleach
import markdown2
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


def render_markdown_safe(markdown_text: str) -> str:
    """
    Преобразует текст с Markdown в HTML с использованием
    библиотеки markdown2 и bleach для удаления неразрешенных HTML-тегов.
    """

    # Преобразование текста Markdown -> HTML:
    #   - fenced-code-blocks: поддержка блоков кода с тройными кавычками ```
    #   - tables: поддержка Markdown-таблиц
    #   - strike: поддержка зачеркнутого текста
    #   - task_list: поддержка списков задач - [ ] / - [x]
    html = markdown2.markdown(
        markdown_text, extras=["fenced-code-blocks", "tables", "strike", "task_list"]
    )

    # Множество безопасных HTML-тегов
    allowed_tags = {
        "p",
        "strong",
        "em",
        "ul",
        "ol",
        "li",
        "a",
        "img",
        "pre",
        "code",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "hr",
        "br",
        "table",
        "thead",
        "tbody",
        "tr",
        "th",
        "td",
        "blockquote",
        "sub",
        "sup",
        "del",
        "kbd",
        "details",
        "summary",
    }

    # Множество безопасных атрибутов HTML-тегов
    allowed_attrs = {
        "*": ["class", "id"],
        "a": ["href", "title", "rel", "target"],
        "img": ["src", "alt", "title", "loading"],
        "code": ["class"],
        "details": ["open"],
    }

    # Очистка HTML от неразрешенных HTML-тегов и их атрибутов
    safe_html = bleach.clean(html, tags=allowed_tags, attributes=allowed_attrs, strip=True)

    return safe_html
