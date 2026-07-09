from allauth.account.auth_backends import AuthenticationBackend
from django.contrib.auth.backends import ModelBackend


class CustomAuthenticationBackend(ModelBackend):
    """
    Переопределяет стандартный бекенд аутентификации Django через сессию.

    Добавляет проверку, что пользователь не заблокирован.
    """

    def user_can_authenticate(self, user):
        return super().user_can_authenticate(user) and not user.is_blocked


class CustomAllAuthAuthenticationBackend(AuthenticationBackend):
    """
    Переопределяет стандартный бекенд аутентификации django-allauth.

    Добавляет проверку, что пользователь не заблокирован.
    """

    def user_can_authenticate(self, user):
        return super().user_can_authenticate(user) and not user.is_blocked
