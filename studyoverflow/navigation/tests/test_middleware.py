from types import SimpleNamespace

import pytest
from django.http import HttpResponse
from django.test import RequestFactory

from navigation.middleware import RequestSourceMiddleware, UserActivityMiddleware


@pytest.fixture
def request_factory():
    """Фабрика запросов для создания объектов request."""
    return RequestFactory()


class TestUserActivityMiddleware:
    """Тестирование middleware для логирования активности пользователей."""

    @pytest.mark.parametrize(
        "path, expected_status",
        [
            ("/health/", 200),
            ("/ws/notifications/", 101),
        ],
    )
    def test_skips_excluded_paths(self, path, expected_status, request_factory, mocker):
        """
        Запросы по исключенным путям (например, /health) не логируются.
        """
        mock_get_response = mocker.Mock(return_value=HttpResponse(status=expected_status))
        mock_logger = mocker.patch("navigation.middleware.logger")

        middleware_health = UserActivityMiddleware(mock_get_response)

        request = request_factory.get(path)

        response = middleware_health(request)

        assert response.status_code == expected_status
        mock_get_response.assert_called_once_with(request)
        mock_logger.info.assert_not_called()

    def test_logs_anonymous_user_request(self, request_factory, mocker):
        """Для неавторизованного пользователя в лог передаются None для данных пользователя."""
        mock_get_response = mocker.Mock(return_value=HttpResponse(status=200))
        mock_logger = mocker.patch("navigation.middleware.logger")

        middleware = UserActivityMiddleware(mock_get_response)
        request = request_factory.get("/some-page/")
        # Анонимный пользователь
        request.user = SimpleNamespace(is_authenticated=False)

        response = middleware(request)

        assert response.status_code == 200
        mock_logger.info.assert_called_once_with(
            "Отправлен запрос к ресурсу.",
            extra={
                "user_id": None,
                "username": None,
                "method": "GET",
                "path": "/some-page/",
                "event_type": "request",
                "response_status_code": 200,
            },
        )

    def test_logs_authenticated_user_request(self, request_factory, mocker):
        """Для авторизованного пользователя логируются его pk, username и статус ответа."""
        mock_get_response = mocker.Mock(return_value=HttpResponse(status=200))
        mock_logger = mocker.patch("navigation.middleware.logger")

        middleware = UserActivityMiddleware(mock_get_response)
        request = request_factory.get("/api/v1/posts/")

        request.user = SimpleNamespace(is_authenticated=True, pk=1, username="test_user")

        response = middleware(request)

        assert response.status_code == 200
        mock_logger.info.assert_called_once_with(
            "Отправлен запрос к ресурсу.",
            extra={
                "user_id": 1,
                "username": "test_user",
                "method": "GET",
                "path": "/api/v1/posts/",
                "event_type": "request",
                "response_status_code": 200,
            },
        )


class TestRequestSourceMiddleware:
    """Тестирование middleware для определения источника запроса web/api."""

    @pytest.mark.parametrize(
        "path,expected_source",
        [
            ("/api/v1/posts/", "api"),
            ("/posts/", "web"),
            ("/", "web"),
        ],
    )
    def test_marks_request_source_correctly(self, path, expected_source, request_factory, mocker):
        """Атрибут source_for_logging корректно устанавливается в зависимости от пути запроса."""
        mock_get_response = mocker.Mock(return_value=HttpResponse(status=200))
        middleware = RequestSourceMiddleware(mock_get_response)

        request = request_factory.get(path)
        middleware(request)

        mock_get_response.assert_called_once_with(request)

        assert hasattr(request, "source_for_logging")
        assert request.source_for_logging == expected_source
