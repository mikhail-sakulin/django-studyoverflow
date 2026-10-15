import fakeredis
import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from factories import (
    CommentFactory,
    LikeFactory,
    NotificationPostCreateFactory,
    PostFactory,
    UserFactory,
)


@pytest.fixture
def user_factory():
    return UserFactory


@pytest.fixture
def post_factory():
    return PostFactory


@pytest.fixture
def comment_factory():
    return CommentFactory


@pytest.fixture
def like_factory():
    return LikeFactory


@pytest.fixture
def notification_post_factory():
    return NotificationPostCreateFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture(autouse=True)
def fake_redis(mocker):
    """
    Подменяет подключение к Redis через fakeredis и возвращает его.

    В OnlineStatusMiddleware, если пользователь аутентифицирован,
    есть обращение к сервисной функции set_user_online, в которой есть прямое обращение к Redis.
    Для OnlineStatusMiddleware достаточно только самой подмены с autouse=True.

    Имитация сервера Redis в оперативной памяти для тестов,
    мок используется для подмены Redis при прямом обращении к Redis.

    Это Fake подмена (полноценная рабочая реализация) через Python-объект.
    """
    redis = fakeredis.FakeStrictRedis(server=fakeredis.FakeServer())
    mocker.patch(
        "users.services.online.get_redis_connection",
        return_value=redis,
    )
    return redis


@pytest.fixture(autouse=True)
def mock_notify_dispatch(mocker):
    """
    Мок Celery-задачи send_channel_notify_event отправки обновления
    счетчика уведомлений через WebSocket, чтобы в тестах не выполнялись обращения к Redis.

    Эта задача объявлена с base=QueueOnce (библиотека celery-once), где переопределен метод
    .apply_async() (.delay() не переопределен, он просто вызывает переопределенный .apply_async()),
    который создает ключ-замок в Redis для предотвращения дублей задачи с одними и теми же
    параметрами. Обращения к Redis происходят при постановке задачи в очередь.

    Celery-задачи запускаются через transaction.on_commit. В тестах при необходимости используется
    фикстура django_capture_on_commit_callbacks из pytest-django, поэтому Celery-задачи могут
    запускаться и в тестах, поэтому apply_async данной задачи мокается, чтобы не было
    обращений в Redis.
    """
    return mocker.patch("notifications.tasks.send_channel_notify_event.apply_async")


@pytest.fixture
def assert_login_required(client, api_client):
    """
    Фикстура для проверки LoginRequired для эндпоинтов.

    Поддерживает как обычные веб-страницы (Django Views с редиректом 302),
    так и API-эндпоинты (DRF Views с кодом 401 Unauthorized).
    """

    def _assert(url_name, url_kwargs=None, method="get", is_api=False):
        # Для текущей реализации тестирования без тела запроса можно было бы использовать
        # только client и для web, и для api запросов.
        test_client = api_client if is_api else client

        url = reverse(url_name, kwargs=url_kwargs)

        # Задается метод тестового клиента для будущего вызова (get, post, delete и т.д.)
        client_method = getattr(test_client, method.lower())
        response = client_method(url)

        if is_api:
            # Для API статус 401 (Unauthorized)
            assert response.status_code == 401
            # Проверка ответа в формате JSON
            assert "application/json" in response.headers.get("Content-Type", "")
        else:
            # Для web поверка редиректа на страницу входа с get-параметром next
            assert response.status_code == 302
            assert reverse("users:login") in response.url
            assert "next=" in response.url

    return _assert


@pytest.fixture
def assert_not_found(client, api_client):
    """
    Фикстура для проверки ответа 404 (Not Found).

    Поддерживает как обычные веб-страницы (Django Views),
    так и API-эндпоинты (DRF Views).
    """

    def _assert(url_name, url_kwargs=None, method="get", is_api=False):
        # Для текущей реализации тестирования без тела запроса можно было бы использовать
        # только client и для web, и для api запросов.
        test_client = api_client if is_api else client

        url = reverse(url_name, kwargs=url_kwargs)

        client_method = getattr(test_client, method.lower())
        response = client_method(url)

        assert response.status_code == 404

        if is_api:
            assert "application/json" in response.get("Content-Type", "")
            assert "detail" in response.data

    return _assert
