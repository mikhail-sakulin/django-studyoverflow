"""
Тесты для модуля domain приложения posts.
"""

from django.test import TestCase
from posts.services.domain import generate_slug


class GenerateSlugTestCase(TestCase):
    def test_normal_russian_text(self):
        self.assertEqual(generate_slug("Новый заголовок"), "novyjj-zagolovok")
        self.assertEqual(generate_slug("Привет мир"), "privet-mir")

    def test_mixed_text(self):
        self.assertEqual(generate_slug("Привет World"), "privet-world")

    def test_text_with_symbols(self):
        self.assertEqual(generate_slug("Тест!@#$%^&*()"), "test")

    def test_long_title_truncation(self):
        long_title = "в" * 300
        slug = generate_slug(long_title, max_length=255)
        self.assertTrue(len(slug) == 255)

    def test_non_string_input(self):
        with self.assertRaises(TypeError):
            generate_slug(None)  # type: ignore
        with self.assertRaises(TypeError):
            generate_slug(12345)  # type: ignore
        with self.assertRaises(TypeError):
            generate_slug(["список"])  # type: ignore
