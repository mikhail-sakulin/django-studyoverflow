from django.utils import timezone
from rest_framework.authentication import (
    SessionAuthentication,
    TokenAuthentication,
)
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication


class BlockedUserMixin:
    """
    Проверяет, что пользователь не заблокирован.
    """

    @staticmethod
    def _check_blocked(user):
        if user.is_blocked:
            if user.blocked_at:
                local_date = timezone.localtime(user.blocked_at)
                date = local_date.strftime("%d.%m.%Y г. %H:%M")
            else:
                date = "неизвестно"

            raise AuthenticationFailed(f"Ваш аккаунт заблокирован {date}.")


class CustomSessionAuthentication(BlockedUserMixin, SessionAuthentication):
    """
    Кастомная аутентификация по сессии с проверкой, что пользователь не заблокирован.
    """

    def authenticate(self, request):
        result = super().authenticate(request)

        if result is None:
            return None

        user, auth = result

        self._check_blocked(user)

        return user, auth


class CustomTokenAuthentication(BlockedUserMixin, TokenAuthentication):
    """
    Кастомная аутентификация по DRF токену с проверкой, что пользователь не заблокирован.
    """

    def authenticate_credentials(self, key):
        user, token = super().authenticate_credentials(key)

        self._check_blocked(user)

        return user, token


class CustomJWTAuthentication(BlockedUserMixin, JWTAuthentication):
    """
    Кастомная аутентификация по JWT токену с проверкой, что пользователь не заблокирован.
    """

    def get_user(self, validated_token):
        user = super().get_user(validated_token)

        self._check_blocked(user)

        return user
