"""
Кастомные фильтры и теги HTML-шаблонов приложения posts.
"""

from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

from posts.services.text_processing import render_markdown_safe


register = template.Library()


@register.filter
# text (именно первый аргумент) перед передачей в функцию будет преобразован в строку
@stringfilter
def markdown_safe(text: str) -> str:
    """
    Фильтр для преобразования текста с Markdown разметкой в безопасный HTML.

    В данный момент фильтр в проекте не используется, поскольку отрендеренный HTML
    сохраняется в БД (поле rendered_content моделей), а не генерируется каждый раз заново.
    """
    if not text:
        return ""

    html_content = render_markdown_safe(text)
    return mark_safe(html_content)
