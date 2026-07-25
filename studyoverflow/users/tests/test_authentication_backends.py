from types import SimpleNamespace

import pytest

from users.authentication_backends import (
    CustomAllAuthAuthenticationBackend,
    CustomAuthenticationBackend,
)


class TestCustomAuthenticationBackends:
    """Тестирование переопределенных Django бекендов аутентификации."""

    @pytest.mark.parametrize(
        "backend_class",
        [CustomAuthenticationBackend, CustomAllAuthAuthenticationBackend],
    )
    def test_user_can_authenticate_active_and_not_blocked(self, backend_class):
        """Активный и незаблокированный пользователь успешно проходит проверку."""
        backend = backend_class()

        user = SimpleNamespace(is_active=True, is_blocked=False)

        assert backend.user_can_authenticate(user) is True

    @pytest.mark.parametrize(
        "backend_class",
        [CustomAuthenticationBackend, CustomAllAuthAuthenticationBackend],
    )
    def test_user_cannot_authenticate_if_blocked(self, backend_class):
        """Заблокированный пользователь не проходит проверку."""
        backend = backend_class()
        user = SimpleNamespace(is_active=True, is_blocked=True)

        assert backend.user_can_authenticate(user) is False

    @pytest.mark.parametrize(
        "backend_class",
        [CustomAuthenticationBackend, CustomAllAuthAuthenticationBackend],
    )
    def test_user_cannot_authenticate_if_inactive(self, backend_class):
        """Неактивный пользователь не проходит проверку (проверка вызова super)."""
        backend = backend_class()
        user = SimpleNamespace(is_active=False, is_blocked=False)

        assert backend.user_can_authenticate(user) is False
