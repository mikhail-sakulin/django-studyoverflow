from types import SimpleNamespace

import pytest
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed
from users.api.authentication import (
    BlockedUserMixin,
    CustomJWTAuthentication,
    CustomSessionAuthentication,
    CustomTokenAuthentication,
)


class TestBlockedUserMixin:

    def test_active_user_passes(self):
        """Незаблокированный пользователь проходит проверку без вызова AuthenticationFailed."""
        user = SimpleNamespace(is_blocked=False)

        BlockedUserMixin._check_blocked(user)

    def test_blocked_user_with_date_raises_error(self):
        """Если пользователь заблокирован, вызывается AuthenticationFailed."""
        now = timezone.now()
        user = SimpleNamespace(is_blocked=True, blocked_at=now)

        with pytest.raises(AuthenticationFailed) as exc:
            BlockedUserMixin._check_blocked(user)

        expected_date = timezone.localtime(now).strftime("%d.%m.%Y г. %H:%M")
        assert f"Ваш аккаунт заблокирован {expected_date}." in str(exc.value.detail)


class TestCustomAuthenticationClasses:
    """Тестирование переопределенных классов аутентификации DRF."""

    def test_session_auth_blocked_user(self, mocker):
        """CustomSessionAuthentication блокирует доступ для заблокированного пользователя."""
        auth = CustomSessionAuthentication()
        user = SimpleNamespace(is_blocked=True, blocked_at=None)

        # Мок родительского метода super().authenticate
        mocker.patch(
            "rest_framework.authentication.SessionAuthentication.authenticate",
            return_value=(user, None),
        )

        with pytest.raises(AuthenticationFailed):
            auth.authenticate(mocker.Mock())

    def test_token_auth_blocked_user(self, mocker):
        """CustomTokenAuthentication блокирует доступ для заблокированного пользователя."""
        auth = CustomTokenAuthentication()
        user = SimpleNamespace(is_blocked=True, blocked_at=None)

        mocker.patch(
            "rest_framework.authentication.TokenAuthentication.authenticate_credentials",
            return_value=(user, "token_obj"),
        )

        with pytest.raises(AuthenticationFailed):
            auth.authenticate_credentials("test_token_key")

    def test_jwt_auth_blocked_user(self, mocker):
        """CustomJWTAuthentication блокирует доступ для заблокированного пользователя."""
        auth = CustomJWTAuthentication()
        user = SimpleNamespace(is_blocked=True, blocked_at=None)

        mocker.patch(
            "rest_framework_simplejwt.authentication.JWTAuthentication.get_user", return_value=user
        )

        with pytest.raises(AuthenticationFailed):
            auth.get_user(mocker.Mock())
