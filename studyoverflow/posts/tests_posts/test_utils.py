from django.test import TestCase
from posts.services.utils import translit_rus_to_eng


class TranslitTestCase(TestCase):
    def test_normal_russian_text(self):
        self.assertEqual(translit_rus_to_eng("Привет, мир!"), "privet, mir!")
        self.assertEqual(translit_rus_to_eng("Ёж"), "jozh")

    def test_engish_text(self):
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
