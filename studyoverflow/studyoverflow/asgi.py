"""
ASGI config for studyoverflow project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application


# Задает переменную окружения со значением "studyoverflow.settings", если она не была задана ранее,
# данная переменная окружения нужна внутренним механизмам Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "studyoverflow.settings")

# Инициализация ASGI HTTP-приложения Django
asgi_application = get_asgi_application()

# Маршруты вебсокетов импортируются после инициализации приложения, так как в routing
# могут импортироваться модели. При создании моделей отрабатывает внутренний механизм (реестр
# приложений (apps)), для работы которого должно быть инициализировано приложение.
import notifications.routing


# Маршрутизатор протоколов, выбор приложения-обработчика для запросов зависит от протокола
# соединения.
application = ProtocolTypeRouter(
    {
        "http": asgi_application,
        # 1) AllowedHostsOriginValidator - слой безопасности, проверяет HTTP-заголовок Origin при
        # попытке установить вебсокет соединение, с чужого сайта соединение не получится открыть.
        # В Origin указан домен сайта, с которого через js-код был отправлен запрос.
        # 2) AuthMiddlewareStack - слой авторизации, аналог AuthenticationMiddleware, который
        # считывает токен сессии sessionid из cookies. Работает только со стандартными сессиями,
        # для авторизации по DRF токену или по JWT токену нужно писать свой Middleware, считывать
        # токен, находить пользователя и задавать его в scope['user'].
        # 3) При установлении WebSocket соединения сначала идет HTTP GET-запрос с заголовками
        # Connection: Upgrade и Upgrade: websocket, Daphne парсит заголовки до того, как передать
        # запрос в asgi.py. При обработке запроса его протокол (scope["type"]) уже будет
        # равен "websocket".
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(
                # Слой маршрутизации, аналог urls.py
                URLRouter(notifications.routing.websocket_urlpatterns)
            ),
        ),
    }
)
