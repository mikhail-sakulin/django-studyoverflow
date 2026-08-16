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
        # экранирование кавычек ('hello')
        assert "print(&#39;hello&#39;)" in html

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
