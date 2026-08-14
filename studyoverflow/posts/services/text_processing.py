"""
Утилиты для обработки текста и контента приложения posts.
"""

import html
import re

import bleach
import markdown2
from bleach.css_sanitizer import CSSSanitizer
from django.utils.html import strip_tags
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


def strip_tags_and_whitespace_chars_from_html(html_text: str) -> str:
    """
    Очищает html текст от html тегов и заменяет все пробельные символы (пробел, табуляция,
    перевод строки и так далее) одиночными пробелами.
    """
    # Добавляет пробел после закрывающей скоки тега, чтобы текст из соседних тегов не сливался
    text_with_spaces = re.sub(r">", "> ", html_text)

    clean_tags_text = strip_tags(text_with_spaces)

    # Заменяет HTML-сущности на текстовые символы, коды символов заменяются символами
    unescaped_text = html.unescape(clean_tags_text)

    return re.sub(r"\s+", " ", unescaped_text).strip()


def render_markdown_safe(markdown_text: str) -> str:
    """
    Преобразует текст с Markdown в HTML с использованием
    библиотеки markdown2 и bleach для удаления неразрешенных HTML-тегов.
    """
    # Если один из блоков с кодом не закрыт, то в конец добавляется закрытие ```
    if markdown_text.count("```") % 2 != 0:
        markdown_text += "\n```"

    # Заменяет неразрывные пробелы на обычные
    markdown_text = markdown_text.replace("\xa0", " ")

    # Преобразование текста Markdown -> HTML:
    #   - fenced-code-blocks: поддержка блоков кода с тройными кавычками ```
    #   - tables: поддержка Markdown-таблиц
    #   - strike: поддержка зачеркнутого текста
    #   - task_list: поддержка списков задач - [ ] / - [x]
    #   - footnotes: поддержка сносок
    html = markdown2.markdown(
        markdown_text, extras=["fenced-code-blocks", "tables", "strike", "task_list", "footnotes"]
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
        "div",
    }

    # Разрешается свойство text-align в style для тегов "th" и "td"
    css_sanitizer = CSSSanitizer(allowed_css_properties=["text-align"])

    # Множество безопасных атрибутов HTML-тегов
    allowed_attrs = {
        "*": ["class", "id"],
        "a": ["href", "title", "rel", "target", "rev"],
        "img": ["src", "alt", "title", "loading"],
        "code": ["class"],
        "details": ["open"],
        "input": ["class", "type", "checked", "disabled"],
        "th": ["style"],
        "td": ["style"],
    }

    # Очистка HTML от неразрешенных HTML-тегов и их атрибутов
    safe_html = bleach.clean(
        html,
        tags=allowed_tags,
        attributes=allowed_attrs,
        css_sanitizer=css_sanitizer,
        protocols=["http", "https", "mailto"],
        strip=True,
    )

    # rel="nofollow" - защита от спама и SEO-атрибут (сайт не ручается за ссылки от пользователей)
    # target="_blank" - заставляет браузер открывать ссылку в новой вкладке
    safe_html = bleach.linkify(
        safe_html,
        callbacks=[bleach.callbacks.nofollow, bleach.callbacks.target_blank],
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
