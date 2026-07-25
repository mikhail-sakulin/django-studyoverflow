from types import SimpleNamespace

import pytest
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import RequestFactory
from django.urls import reverse

from users.middleware import BlockedUserMiddleware, OnlineStatusMiddleware


@pytest.fixture
def get_response():
    """Заглушка (stub) для имитации ответа от следующего слоя middleware или view."""
    return lambda request: HttpResponse()


@pytest.fixture
def request_factory():
    """Фабрика запросов для создания объектов request."""
    return RequestFactory()


class TestOnlineStatusMiddleware:
    def test_authenticated_user_calls_set_online(self, request_factory, mocker, get_response):
        """Если пользователь аутентифицирован, вызывается обновление статуса в Redis."""
        middleware = OnlineStatusMiddleware(get_response)
        request = request_factory.get("/")

        # Stub для объекта пользователя
        request.user = SimpleNamespace(is_authenticated=True, pk=5)

        mock_set_online = mocker.patch("users.middleware.set_user_online")

        response = middleware(request)

        assert response.status_code == 200
        mock_set_online.assert_called_once_with(5)

    def test_anonymous_user_ignores_set_online(self, request_factory, mocker, get_response):
        """Для анонимных пользователей функция обновления статуса не вызывается."""
        middleware = OnlineStatusMiddleware(get_response)
        request = request_factory.get("/")
        request.user = AnonymousUser()

        mock_set_online = mocker.patch("users.middleware.set_user_online")

        response = middleware(request)

        assert response.status_code == 200
        mock_set_online.assert_not_called()


class TestBlockedUserMiddleware:
    def test_api_request_is_ignored(self, request_factory, mocker, get_response):
        """Запросы к API (/api/) пропускаются без проверок блокировки пользователя."""
        middleware = BlockedUserMiddleware(get_response)
        request = request_factory.get("/api/users/me/")

        request.user = SimpleNamespace(is_authenticated=True, is_blocked=True)

        mock_logout = mocker.patch("users.middleware.logout")

        response = middleware(request)

        assert response.status_code == 200
        mock_logout.assert_not_called()

    def test_blocked_user_is_logged_out_and_redirected(self, request_factory, mocker, get_response):
        """Для заблокированного пользователя очищается сессия и возвращается редирект на home."""
        middleware = BlockedUserMiddleware(get_response)
        request = request_factory.get("/")
        request.user = SimpleNamespace(is_authenticated=True, is_blocked=True)

        mock_logout = mocker.patch("users.middleware.logout")
        mock_messages = mocker.patch("users.middleware.messages.error")

        response = middleware(request)

        assert response.status_code == 302
        assert response.url == reverse("home")
        mock_logout.assert_called_once_with(request)
        mock_messages.assert_called_once()

    def test_active_user_passes_through(self, request_factory, mocker, get_response):
        """Незаблокированный пользователь проходит middleware без logout и редиректа."""
        middleware = BlockedUserMiddleware(get_response)
        request = request_factory.get("/")
        request.user = SimpleNamespace(is_authenticated=True, is_blocked=False)

        mock_logout = mocker.patch("users.middleware.logout")

        response = middleware(request)

        assert response.status_code == 200
        mock_logout.assert_not_called()

    def test_anonymous_user_passes_through(self, request_factory, mocker, get_response):
        """Анонимный пользователь имеет доступ к открытым ресурсам."""
        middleware = BlockedUserMiddleware(get_response)
        request = request_factory.get("/")
        request.user = AnonymousUser()

        mock_logout = mocker.patch("users.middleware.logout")

        response = middleware(request)

        assert response.status_code == 200
        mock_logout.assert_not_called()
