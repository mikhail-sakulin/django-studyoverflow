from django.apps import AppConfig


class NavigationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "navigation"

    def ready(self):
        """Выполняется после загрузки приложений."""
        # Кастомные схемы аутентификации, импорт для автоматической регистрации в Swagger
        import navigation.api.swagger_extensions  # noqa: F401
