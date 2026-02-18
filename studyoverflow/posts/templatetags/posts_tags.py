"""
Кастомные фильтры и теги HTML-шаблонов приложения posts.
"""

from django import template
from django.template.defaultfilters import stringfilter
from posts.services import render_markdown_safe


register = template.Library()


@register.filter
@stringfilter
def markdown_safe(text: str) -> str:
    """Фильтр для преобразования текста с Markdown разметкой в безопасный HTML."""
    return render_markdown_safe(text)
