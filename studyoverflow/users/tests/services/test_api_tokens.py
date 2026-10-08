import pytest
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from rest_framework_simplejwt.tokens import RefreshToken

from users.services.api_tokens import revoke_user_api_tokens


@pytest.mark.django_db
class TestRevokeUserApiTokens:
    """Тестирование сервиса revoke_user_api_tokens."""

    def test_deletes_drf_token(self, user_factory):
        """DRF-токен пользователя удаляется."""
        user = user_factory()
        Token.objects.create(user=user)

        revoke_user_api_tokens(user)

        assert not Token.objects.filter(user=user).exists()

    def test_blacklists_all_refresh_tokens(self, user_factory):
        """Все refresh JWT-токены пользователя вносятся в blacklist."""
        user = user_factory()
        refresh_tokens = [RefreshToken.for_user(user) for _ in range(3)]

        revoke_user_api_tokens(user)

        assert OutstandingToken.objects.filter(user=user).count() == 3
        assert BlacklistedToken.objects.filter(token__user=user).count() == 3
        for refresh in refresh_tokens:
            # RefreshToken создает python-объект токена из его строкового представления,
            # при этом валидируя токен. При недействительном токене вызывается TokenError.
            #
            # Альтернатива через прямой запрос к БД:
            #   assert BlacklistedToken.objects.filter(token__jti=refresh["jti"]).exists()
            with pytest.raises(TokenError):
                refresh.check_blacklist()

    def test_already_blacklisted_tokens_are_skipped(self, user_factory):
        """Уже заблокированные refresh JWT-токены не вызывают исключения."""
        user = user_factory()
        already_blacklisted = RefreshToken.for_user(user)
        already_blacklisted.blacklist()
        RefreshToken.for_user(user)

        revoke_user_api_tokens(user)

        assert OutstandingToken.objects.filter(user=user).count() == 2
        assert BlacklistedToken.objects.filter(token__user=user).count() == 2

    def test_is_idempotent(self, user_factory):
        """Повторный вызов сервиса не вызывает исключений и не создает дубли."""
        user = user_factory()
        Token.objects.create(user=user)
        RefreshToken.for_user(user)

        revoke_user_api_tokens(user)
        revoke_user_api_tokens(user)

        assert not Token.objects.filter(user=user).exists()
        assert BlacklistedToken.objects.filter(token__user=user).count() == 1

    def test_user_without_tokens(self, user_factory):
        """Если у пользователя нет токенов, исключения не вызываются."""
        user = user_factory()

        revoke_user_api_tokens(user)

        assert not Token.objects.filter(user=user).exists()
        assert not BlacklistedToken.objects.filter(token__user=user).exists()
