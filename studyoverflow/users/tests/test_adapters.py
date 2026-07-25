from types import SimpleNamespace

import pytest
from allauth.core.exceptions import ImmediateHttpResponse
from django.test import RequestFactory
from rest_framework.exceptions import PermissionDenied
from users.adapters import CustomSocialAccountAdapter


@pytest.fixture
def request_factory():
    """Фабрика запросов для создания объектов request."""
    return RequestFactory()


class TestCustomSocialAccountAdapter:
    """Тесты логики адаптеров для входа через социальные сети."""

    def test_pre_social_login_blocked_user_web(self, request_factory, mocker):
        """
        Web-запрос (не api) от заблокированного пользователя
        прерывается редиректом (ImmediateHttpResponse).
        """
        adapter = CustomSocialAccountAdapter()
        request = request_factory.get("/accounts/google/login/callback/")
        user = SimpleNamespace(is_blocked=True, blocked_at=None)
        sociallogin = SimpleNamespace(user=user)

        mock_messages = mocker.patch("users.adapters.messages.error")

        with pytest.raises(ImmediateHttpResponse):
            adapter.pre_social_login(request, sociallogin)

        mock_messages.assert_called_once()

    def test_pre_social_login_blocked_user_api(self, request_factory):
        """API-запрос от заблокированного пользователя вызывает PermissionDenied."""
        adapter = CustomSocialAccountAdapter()
        request = request_factory.get("/api/v1/auth/google/")
        user = SimpleNamespace(is_blocked=True, blocked_at=None)
        sociallogin = SimpleNamespace(user=user)

        with pytest.raises(PermissionDenied) as exc:
            adapter.pre_social_login(request, sociallogin)

        assert "заблокирован" in str(exc.value.detail).lower()

    def test_save_user_triggers_celery_avatar_download(self, mocker):
        """
        Проверка, что после сохранения пользователя запускается Celery-задача на загрузку
        его аватара из соцсети.
        """
        adapter = CustomSocialAccountAdapter()

        mock_user = mocker.MagicMock(is_social=False, pk=1)
        mock_sociallogin = mocker.MagicMock()
        mock_sociallogin.account.provider = "google"
        mock_sociallogin.account.extra_data = {}

        mocker.patch("users.adapters.DefaultSocialAccountAdapter.save_user", return_value=mock_user)

        # Объект словаря не заменяется на Mock, но его ключи и значения перезаписываются.
        mocker.patch.dict(
            "users.adapters.SOCIAL_HANDLERS",
            {"google": lambda user, data: "http://example.com/avatar.jpg"},
        )

        # Немедленное выполнение celery задачи
        mocker.patch("users.adapters.transaction.on_commit", side_effect=lambda func: func())

        mock_task = mocker.patch("users.adapters.download_and_set_avatar.delay")

        adapter.save_user(mocker.Mock(), mock_sociallogin)

        assert mock_user.is_social is True
        mock_user.save.assert_called_once()
        mock_task.assert_called_once_with(mock_user.pk, "http://example.com/avatar.jpg")
