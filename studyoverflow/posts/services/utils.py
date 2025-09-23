"""
Модуль содержит вспомогательные функции для приложения posts.
"""


def translit_rus_to_eng(text: str) -> str:
    """
    Преобразует русские буквы строки в латиницу.

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
