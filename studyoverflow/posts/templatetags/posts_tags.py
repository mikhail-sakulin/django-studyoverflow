"""
Модуль для хранения пользовательских фильтров и тегов HTML-шаблонов приложения posts.
"""

from django import template

from ..services.domain import render_markdown_safe


register = template.Library()


@register.filter
def markdown_safe(text):
    """
    Фильтр для преобразования текста с Markdown разметкой в безопасный HTML.
    """
    return render_markdown_safe(text)
