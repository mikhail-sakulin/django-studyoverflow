from typing import Final

from posts.urls import app_name as posts_app_name
from users.urls import app_name as users_app_name


# Меню сайта для header для base.html
MENU: Final = [
    {"name": "Все посты", "url": f"{posts_app_name}:list"},
    {"name": "Создать пост", "url": f"{posts_app_name}:create"},
    {"name": "Пользователи", "url": f"{users_app_name}:list"},
]
