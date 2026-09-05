import pytest
from django.test import SimpleTestCase

from posts.models import Post
from posts.services import (
    generate_slug,
    normalize_tag_name,
    render_markdown_safe,
    strip_tags_and_whitespace_chars_from_html,
    translit_rus_to_eng,
)
from posts.services.text_processing import (
    _protect_markdown_text_blocks,
    _restore_markdown_text_blocks,
)


class TestNormalizeTagName:
    @pytest.mark.parametrize(
        "input_tag, expected",
        [
            ("Python", "python"),
            ("  Hello World 2  ", "hello_world_2"),
            ("Django    Framework", "django_framework"),
            ("my___tag", "my_tag"),
            ("  cool _ stuff  ", "cool_stuff"),
            ("ONE_two THREE", "one_two_three"),
        ],
    )
    def test_normalize_tag_name(self, input_tag, expected):
        assert normalize_tag_name(input_tag) == expected


@pytest.mark.parametrize(
    ("html_text", "expected"),
    [
        (
            "<p>Hello <strong>Django</strong></p>",
            "Hello Django",
        ),
        (
            "<h1>Django</h1><p>PostgreSQL</p>",
            "Django PostgreSQL",
        ),
        (
            "<p>Hello</p>  \n\n\t<p>Django</p>",
            "Hello Django",
        ),
        (
            "<p>  Hello    Django  </p>",
            "Hello Django",
        ),
    ],
)
def test_strip_tags_and_whitespace_chars_from_html(html_text, expected):
    assert strip_tags_and_whitespace_chars_from_html(html_text) == expected


class TestProtectAndRestoreMarkdownTextBlocks:
    """Тестирование защиты и восстановления блоков текста через плейсхолдеры."""

    def test_protect_replaces_matches_with_placeholders(self):
        """Найденные по паттерну блоки заменяются на плейсхолдеры с заданным префиксом."""
        text = 'before <span class="math-inline">x_1</span> after'
        pattern = r'<span class="math-inline">.*?</span>'

        protected_text, blocks = _protect_markdown_text_blocks(
            text, pattern, placeholder_prefix="MATHINLINEBLOCK"
        )

        assert '<span class="math-inline">' not in protected_text
        assert "before " in protected_text
        assert " after" in protected_text
        assert len(blocks) == 1

        placeholder, original = blocks[0]
        assert placeholder.startswith("MATHINLINEBLOCK")
        assert placeholder in protected_text
        assert original == '<span class="math-inline">x_1</span>'

    def test_protect_handles_multiple_matches_with_unique_placeholders(self):
        """При нескольких совпадениях каждому блоку присваивается уникальный плейсхолдер."""
        text = '<span class="math-inline">a</span> text ' '<span class="math-inline">b</span>'
        pattern = r'<span class="math-inline">.*?</span>'

        protected_text, blocks = _protect_markdown_text_blocks(
            text, pattern, placeholder_prefix="MATHINLINEBLOCK"
        )

        assert len(blocks) == 2
        # Плейсхолдеры уникальны за счёт uuid
        assert blocks[0][0] != blocks[1][0]
        assert blocks[0][1] == '<span class="math-inline">a</span>'
        assert blocks[1][1] == '<span class="math-inline">b</span>'

    def test_protect_matches_across_newlines(self):
        """
        Паттерн находит совпадения, содержащие перенос строки (флаг re.DOTALL - точка
        может означать любой символ, включая символ переноса строки).
        """
        text = '<div class="math">line1\nline2</div>'
        pattern = r'<div class="math">.*?</div>'

        protected_text, blocks = _protect_markdown_text_blocks(
            text, pattern, placeholder_prefix="MATHCENTERBLOCK"
        )

        assert len(blocks) == 1
        assert blocks[0][1] == '<div class="math">line1\nline2</div>'

    def test_protect_no_matches_returns_original_text_and_empty_blocks(self):
        """Если совпадений нет, текст возвращается без изменений, а список блоков пуст."""
        text = "just plain text without protected blocks"
        pattern = r'<span class="math-inline">.*?</span>'

        protected_text, blocks = _protect_markdown_text_blocks(
            text, pattern, placeholder_prefix="MATHINLINEBLOCK"
        )

        assert protected_text == text
        assert blocks == []

    def test_restore_puts_original_blocks_back_in_place_of_placeholders(self):
        """Плейсхолдеры в html корректно заменяются обратно на исходные блоки."""
        blocks = [("PLACEHOLDER1", '<span class="math-inline">x_1</span>')]
        rendered_html = "<p>before PLACEHOLDER1 after</p>"

        restored_html = _restore_markdown_text_blocks(rendered_html, blocks)

        assert restored_html == '<p>before <span class="math-inline">x_1</span> after</p>'

    def test_restore_with_multiple_blocks(self):
        """Восстанавливаются несколько блоков одновременно, каждый по своему плейсхолдеру."""
        blocks = [
            ("PH1", '<span class="math-inline">a</span>'),
            ("PH2", '<span class="math-inline">b</span>'),
        ]
        rendered_html = "<p>PH1 and PH2</p>"

        restored_html = _restore_markdown_text_blocks(rendered_html, blocks)

        assert restored_html == (
            '<p><span class="math-inline">a</span> and ' '<span class="math-inline">b</span></p>'
        )

    def test_protect_then_restore_roundtrip(self):
        """Последовательное применение protect и restore возвращает исходный блок текста."""
        # Двойное экранирование: \\ - для экранирования \, чтобы в тексте буквально было \_,
        # а \_ в LaTeX экранирует _, чтобы "_" воспринимался не как начало текста в нижнем индексе,
        # а как просто нижнее подчеркивание.
        text = 'text <span class="math-inline">a_1 \\_ b</span> more text'
        pattern = r'<span class="math-inline">.*?</span>'

        protected_text, blocks = _protect_markdown_text_blocks(
            text, pattern, placeholder_prefix="MATHINLINEBLOCK"
        )
        restored_text = _restore_markdown_text_blocks(protected_text, blocks)

        assert restored_text == text


class TestRenderMarkdownSafe:
    """Тестирование безопасного рендеринга Markdown в HTML."""

    def test_basic_markdown_rendering(self):
        """Жирный текст и курсив корректно преобразуются в HTML-теги."""
        html = render_markdown_safe("**bold** and *italic*")

        assert "<strong>bold</strong>" in html
        assert "<em>italic</em>" in html

    def test_unsafe_html_stripping(self):
        """Опасные теги вырезаются (strip=True), а безопасные остаются."""
        html = render_markdown_safe("<script>alert('XSS')</script><p>safe text</p>")

        assert "<script>" not in html
        assert "<p>safe text</p>" in html

    def test_javascript_link_stripped(self):
        """Ссылки с javascript-протоколом вырезаются."""
        html = render_markdown_safe("[click](javascript:alert(1))")

        assert "javascript:" not in html
        # ссылка может остаться, но без href или тег <a> удалён
        assert "<a" not in html or 'href="javascript:' not in html

    def test_linkify_and_nofollow_noopener_target_blank(self):
        """Ссылки автоматически получают атрибуты безопасности."""
        html = render_markdown_safe("[Google](https://google.com)")

        # адрес ссылки
        assert 'href="https://google.com"' in html
        # rel="nofollow" - защита от спама и SEO-атрибут (сайт не ручается за
        # ссылки от пользователей)
        assert 'rel="nofollow"' in html
        # заставляет браузер открывать ссылку в новой вкладке
        assert 'target="_blank"' in html

    def test_allowed_attributes_preserved(self):
        """Разрешённые атрибуты id и class не удаляются."""
        html = render_markdown_safe('<p id="5" class="my-class">text</p>')

        assert 'id="5"' in html
        assert 'class="my-class"' in html

    def test_tables_rendering(self):
        """Корректный рендер markdown-таблиц (наличие "tables" в python списке extras)."""
        markdown_table = "| Header |\n" "| ------ |\n" "| Cell   |"
        html = render_markdown_safe(markdown_table)

        assert "<table>" in html
        assert "<th>Header</th>" in html
        assert "<td>Cell</td>" in html

    def test_strike_through_rendering(self):
        """Зачёркнутый текст (наличие "strike" в python списке extras) преобразуется в <s>."""
        html = render_markdown_safe("~~deleted~~")

        assert "<s>deleted</s>" in html

    def test_fenced_code_blocks(self):
        """Блоки кода с тройными кавычками рендерятся в <pre><code>...</code></pre>."""
        code_block = "```python\nprint('hello')\n```"
        html = render_markdown_safe(code_block)

        assert "<pre>" in html or "<pre" in html
        assert "<code" in html
        assert "print('hello')" in html

    def test_task_lists(self):
        """
        Списки задач преобразуются в HTML-инпуты (вывод информации)
        (наличие "task_list" в python списке extras).
        """
        task_list = "- [x] Done\n- [ ] Todo"
        html = render_markdown_safe(task_list)

        assert "input" in html
        assert "type=" in html
        assert "disabled" in html
        assert "checked" in html

    def test_highlightjs_lang_class_added_to_code_block(self):
        """
        К блокам кода с указанием языка добавляется CSS-класс языка
        (например, class="language-python") для интеграции с highlight.js
        (из-за наличия "highlightjs-lang" в python списке extras).
        """
        code_block = "```python\nprint('hello')\n```"
        html = render_markdown_safe(code_block)

        assert 'class="python language-python"' in html

    def test_break_on_newline_converts_single_newline_to_br(self):
        """
        Одиночный перевод строки внутри абзаца превращается в тег <br>
        (проверяется наличие "break-on-newline" в python списке extras).
        """
        text = "line one\nline two"
        html = render_markdown_safe(text)

        assert "<br>" in html

    def test_math_inline_block_is_preserved_as_is(self):
        """
        Inline math-блоки (<span class="math-inline">...</span>) защищаются от обработки
        markdown2 и bleach и сохраняются в исходном виде в итоговом html.
        """
        text = 'Формула: <span class="math-inline">a_1 \\_ b</span> и текст дальше.'
        html = render_markdown_safe(text)

        assert '<span class="math-inline">a_1 \\_ b</span>' in html

    def test_math_center_block_is_preserved_as_is(self):
        """
        Центрированные math-блоки (<div class="math">...</div>) защищаются от обработки
        markdown2 и bleach и сохраняются в исходном виде в итоговом html.
        """
        text = 'Формула:\n<div class="math">x^2 + y^2 = z^2</div>\nдальше текст.'
        html = render_markdown_safe(text)

        assert '<div class="math">x^2 + y^2 = z^2</div>' in html


class TestGenerateSlug(SimpleTestCase):
    def test_normal_russian_text(self):
        self.assertEqual(generate_slug("Новый заголовок"), "novyjj-zagolovok")
        self.assertEqual(generate_slug("Привет мир"), "privet-mir")

    def test_mixed_text(self):
        self.assertEqual(generate_slug("Привет, World"), "privet-world")

    def test_text_with_symbols(self):
        self.assertEqual(generate_slug("Тест!@#$%^&*()"), "test")

    def test_long_title_truncation(self):
        long_title = "в" * (Post.MAX_TITLE_SLUG_LENGTH_POST + 10)
        slug = generate_slug(long_title, max_length=Post.MAX_TITLE_SLUG_LENGTH_POST)
        self.assertEqual(len(slug), Post.MAX_TITLE_SLUG_LENGTH_POST)

    def test_non_string_input(self):
        # Чтобы убрать дублирование, используя unittest, можно использовать
        #     with self.subTest(invalid_input=invalid_input):
        #         with self.assertRaises(TypeError):
        #             generate_slug(invalid_input)
        with self.assertRaises(TypeError):
            generate_slug(None)  # type: ignore
        with self.assertRaises(TypeError):
            generate_slug(12345)  # type: ignore
        with self.assertRaises(TypeError):
            generate_slug(["список"])  # type: ignore

    def test_multilingual_fallback_to_default_slug(self):
        """
        Для заголовка из символов, для которых не настроена транслитерация (например, иероглифы),
        возвращается дефолтный slug 'post'.
        """
        self.assertEqual(generate_slug("投稿のタイトル"), "post")


class TestTranslitRusToEng(SimpleTestCase):
    def test_normal_russian_text(self):
        self.assertEqual(translit_rus_to_eng("Привет, мир!"), "privet, mir!")
        self.assertEqual(translit_rus_to_eng("Ёж"), "jozh")

    def test_english_text(self):
        self.assertEqual(translit_rus_to_eng("cat"), "cat")

    def test_mixed_text(self):
        self.assertEqual(translit_rus_to_eng("dog и кошка"), "dog i koshka")

    def test_uppercase(self):
        self.assertEqual(translit_rus_to_eng("РАСТЕНИЕ"), "rastenie")

    def test_only_symbols(self):
        self.assertEqual(translit_rus_to_eng("!@#$%^&*()"), "!@#$%^&*()")

    def test_none_input(self):
        with self.assertRaises(AttributeError):
            translit_rus_to_eng(None)  # type: ignore

    def test_int_input(self):
        with self.assertRaises(AttributeError):
            translit_rus_to_eng(12)  # type: ignore
