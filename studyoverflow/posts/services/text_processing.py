"""
Утилиты для обработки текста и контента приложения posts.
"""

import re

import bleach
import markdown2
from django.utils.text import slugify


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
        "u",
        "s",
        "input",
    }

    # Множество безопасных атрибутов HTML-тегов
    allowed_attrs = {
        "*": ["class", "id"],
        "a": ["href", "title", "rel", "target"],
        "img": ["src", "alt", "title", "loading"],
        "code": ["class"],
        "details": ["open"],
        "input": ["class", "type", "checked", "disabled"],
    }

    # Очистка HTML от неразрешенных HTML-тегов и их атрибутов
    safe_html = bleach.clean(
        html,
        tags=allowed_tags,
        attributes=allowed_attrs,
        protocols=["http", "https", "mailto"],
        strip=True,
    )

    # Добавление nofollow и noopener к ссылкам
    safe_html = bleach.linkify(
        safe_html,
        callbacks=[bleach.callbacks.nofollow, bleach.callbacks.target_blank],  # rel="noopener"
    )

    return safe_html


def normalize_tag_name(tag_name: str) -> str:
    """
    Приводит имя тега к нормализованному виду:
    - Удаление пробелов по краям.
    - Приведение к нижнему регистру.
    - Замена пробелов на одиночное нижнее подчеркивание.
    - Замена нескольких подряд идущих нижних подчеркиваний на одно.
    """
    tag_name = tag_name.strip().lower()
    tag_name = re.sub(r"\s+", "_", tag_name)
    tag_name = re.sub(r"_+", "_", tag_name)
    return tag_name


def translit_rus_to_eng(text: str) -> str:
    """
    Преобразует русские буквы строки в латиницу в нижнем регистре.

    Пример:
        translit_rus_to_eng("Привет") -> 'privet'
    """

    translit_dict = {
        "а": "a",
        "б": "b",
        "в": "v",
        "г": "g",
        "д": "d",
        "е": "e",
        "ё": "jo",
        "ж": "zh",
        "з": "z",
        "и": "i",
        "й": "jj",
        "к": "k",
        "л": "l",
        "м": "m",
        "н": "n",
        "о": "o",
        "п": "p",
        "р": "r",
        "с": "s",
        "т": "t",
        "у": "u",
        "ф": "f",
        "х": "kh",
        "ц": "c",
        "ч": "ch",
        "ш": "sh",
        "щ": "shh",
        "ъ": "",
        "ы": "y",
        "ь": "",
        "э": "eh",
        "ю": "ju",
        "я": "ja",
    }

    return "".join(translit_dict.get(letter, letter) for letter in text.lower())
