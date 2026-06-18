from django.apps import apps
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken


def customize_jwt_models():
    """Настройка названий моделей и приложения Simple JWT в админ-панели."""
    if not apps.is_installed("rest_framework_simplejwt.token_blacklist"):
        return

    OutstandingToken._meta.verbose_name = "Выданный токен"
    OutstandingToken._meta.verbose_name_plural = "Выданные токены"

    BlacklistedToken._meta.verbose_name = "Заблокированный токен"
    BlacklistedToken._meta.verbose_name_plural = "Заблокированные токены"

    token_blacklist_config = apps.get_app_config("token_blacklist")
    token_blacklist_config.verbose_name = "Авторизация JWT"
