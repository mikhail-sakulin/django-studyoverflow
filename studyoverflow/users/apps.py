from django.apps import AppConfig


class UsersConfig(AppConfig):
    verbose_name = "Пользователи (users)"
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"

    def ready(self):
        """
        Выполняется после загрузки приложений.
        """
        # Регистрация обработчиков сигналов после загрузки приложения.
        import users.signals  # noqa: F401

        # Для JWT токенов: настройка отображения приложения и моделей JWT токенов в админ-панели
        from users.jwt_admin import customize_jwt_models

        customize_jwt_models()
