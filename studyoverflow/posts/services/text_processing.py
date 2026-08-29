"""
Утилиты для обработки текста и контента приложения posts.
"""

import html
import re
import uuid

import bleach
import markdown2
from bleach import Cleaner
from bleach.css_sanitizer import CSSSanitizer
from bleach.linkifier import LinkifyFilter
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
    # Добавляет пробел после закрывающей скобки тега, чтобы текст из соседних тегов не сливался
    text_with_spaces = re.sub(r">", "> ", html_text)

    clean_tags_text = strip_tags(text_with_spaces)

    # Заменяет HTML-сущности на текстовые символы, коды символов заменяются символами
    unescaped_text = html.unescape(clean_tags_text)

    return re.sub(r"\s+", " ", unescaped_text).strip()


def _protect_markdown_text_blocks(
    markdown_text: str, pattern: str, placeholder_prefix: str
) -> tuple[str, list[tuple[str, str]]]:
    r"""
    Заменяет все вхождения pattern на уникальные плейсхолдеры в markdown_text и возвращает
    (изменённый_текст, список_оригинальных_блоков).

    Блок в списке - кортеж из placeholder, удаленный из текста участок.

    Нужен, например, чтобы обратный слеш "\" не удалялся при записи математической inline-записи
    с использованием экранирования нижнего подчеркивания "\_", так как иначе markdown2 удаляет
    обратный слеш в math inline-блоках.
    """
    # Пустой список для пар (placeholder, original)
    blocks = []

    # Вложенная функция вызывается для каждого найденного совпадения с регулярным выражением.
    # match - объект совпадения, который содержит найденный текст.
    # Подчеркивания "_" и другие спецсимволы недопустимы для значения placeholder, чтобы
    # markdown не воспринял их как маркер курсива при рендеринге html.
    def replacer(match):
        # Добавляется uuid_prefix, чтобы пользователь не мог случайно ввести placeholder и получить
        # неожиданный результат. Также каждый математический блок получает уникальный placeholder.
        placeholder = f"{placeholder_prefix}{uuid.uuid4().hex}"
        # Сохраняется пара (placeholder, original)
        blocks.append((placeholder, match.group(0)))
        return placeholder

    # Поиск и замена текста по регулярному выражению.
    # pattern - регулярка, которая находит подходящие для замены блоки, например
    # r'<span class="math-inline">.*?</span>'.
    # replacer - функция, вызываемая для каждого совпадения, в нее передается найденное совпадение
    # (original).
    # markdown_text – исходный текст
    # flags=re.DOTALL - флаг, который позволяет точке "." совпадать с любым символом,
    # включая перенос строки.
    protected_text = re.sub(pattern, replacer, markdown_text, flags=re.DOTALL)

    return protected_text, blocks


def _restore_markdown_text_blocks(rendered_html: str, blocks: list[tuple[str, str]]) -> str:
    """
    Восстанавливает оригинальные блоки на место плейсхолдеров в html.
    """
    # Заменяет все placeholder в html на original
    for placeholder, original in blocks:
        rendered_html = rendered_html.replace(placeholder, original)

    return rendered_html


def render_markdown_safe(markdown_text: str) -> str:
    """
    Преобразует текст с Markdown в HTML с использованием
    библиотек markdown2 и bleach для удаления неразрешенных HTML-тегов.
    """
    # Если один из блоков с кодом не закрыт, то в конец добавляется закрытие ```
    if markdown_text.count("```") % 2 != 0:
        markdown_text += "\n```"

    # Заменяет неразрывные пробелы на обычные
    markdown_text = markdown_text.replace("\xa0", " ")

    # Защита math-inline блоков - блоки вырезаются из markdown_text перед рендером текста в html,
    # после рендера блоки буду вставлены в html в исходном виде.
    math_inline_pattern = r'<span class="math-inline">.*?</span>'

    protected_text, math_inline_blocks = _protect_markdown_text_blocks(
        markdown_text, math_inline_pattern, placeholder_prefix="MATHINLINEBLOCK"
    )

    # Защита math-center блоков - блоки вырезаются из markdown_text перед рендером текста в html,
    # после рендера блоки буду вставлены в html в исходном виде.
    math_center_pattern = r'<div class="math">.*?</div>'

    protected_text, math_center_blocks = _protect_markdown_text_blocks(
        protected_text, math_center_pattern, placeholder_prefix="MATHCENTERBLOCK"
    )

    # Преобразование текста Markdown -> HTML:
    #   - fenced-code-blocks: поддержка блоков кода с тройными кавычками ```
    #   -  добавляет CSS-класс языка (например, class="language-python") к блокам кода
    #      для интеграции с highlight.js для подсветки кода
    #   - tables: поддержка Markdown-таблиц
    #   - strike: поддержка зачеркнутого текста
    #   - task_list: поддержка списков задач - [ ] / - [x]
    #   - footnotes: поддержка сносок
    #   - break-on-newline: любой одиночный перевод строки внутри абзаца превращается в тег <br>
    rendered_html = markdown2.markdown(
        protected_text,
        extras=[
            "fenced-code-blocks",
            "highlightjs-lang",
            "tables",
            "strike",
            "task_list",
            "footnotes",
            "break-on-newline",
        ],
    )

    rendered_html = _restore_markdown_text_blocks(rendered_html, math_inline_blocks)
    rendered_html = _restore_markdown_text_blocks(rendered_html, math_center_blocks)

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
        "span",
    }

    # Разрешается свойство text-align в style для тегов "th" и "td"
    css_sanitizer = CSSSanitizer(allowed_css_properties=["text-align"])

    # Множество безопасных атрибутов HTML-тегов
    allowed_attrs = {
        "*": ["class", "id"],
        "a": ["href", "title", "rel", "target", "rev"],
        "img": ["src", "alt", "title", "loading", "width", "height"],
        "code": ["class"],
        "details": ["open"],
        "input": ["class", "type", "checked", "disabled"],
        "th": ["style"],
        "td": ["style"],
    }

    # # Очистка HTML от неразрешенных HTML-тегов и их атрибутов
    # safe_html = bleach.clean(
    #     html,
    #     tags=allowed_tags,
    #     attributes=allowed_attrs,
    #     css_sanitizer=css_sanitizer,
    #     protocols=["http", "https", "mailto"],
    #     strip=True,
    # )
    #
    # # rel="nofollow" - защита от спама и SEO-атрибут (сайт не ручается за ссылки от пользователей)
    # # target="_blank" - заставляет браузер открывать ссылку в новой вкладке
    # safe_html = bleach.linkify(
    #     safe_html,
    #     callbacks=[bleach.callbacks.nofollow, bleach.callbacks.target_blank],
    #     #skip_tags=["pre", "code"],
    # )

    # Очистка HTML от неразрешенных HTML-тегов и их атрибутов и создание ссылок из URL выполняются
    # за одно выполнение парсинга через Cleaner с фильтром LinkifyFilter.
    #
    # Ранее осуществлялись раздельные вызовы bleach.clean(), а затем bleach.linkify(). Это
    # ломало HTML-сущности внутри <pre>, например было повторное экранирование символа "&",
    # который мог появиться после экранирования других символов.
    cleaner = Cleaner(
        tags=allowed_tags,
        attributes=allowed_attrs,
        css_sanitizer=css_sanitizer,
        protocols=["http", "https", "mailto"],
        strip=True,
        filters=[
            lambda source: LinkifyFilter(
                source,
                # rel="nofollow" - защита от спама, сайт не ручается за ссылки от пользователей,
                # нужна только для информирования поисковых роботов
                # target="_blank" - заставляет браузер открывать ссылку в новой вкладке
                callbacks=[bleach.callbacks.nofollow, bleach.callbacks.target_blank],
                # Не создавать ссылки из URL внутри блоков кода
                skip_tags=["pre", "code"],
            )
        ],
    )

    safe_html = cleaner.clean(rendered_html)

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
