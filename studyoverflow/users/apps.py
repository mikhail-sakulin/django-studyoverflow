from django.apps import AppConfig
from django.db.models.signals import post_migrate


class UsersConfig(AppConfig):
    verbose_name = "Пользователи (users)"
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"

    def ready(self):
        """
        Выполняется после загрузки приложений.
        """
        # Регистрация обработчиков сигналов после загрузки приложения.
        from users import signals  # noqa: F401

        # Ручная регистрация сигнала
        post_migrate.connect(
            signals.sync_default_groups,
            sender=self,
            # ID сигнала для этого приложения, гарантирует, что функция будет привязана к
            # событию post_migrate ровно один раз, чтобы, если вдруг будет вторая ручная миграция,
            # сигнал не отработал на событие дважды.
            #
            # Декоратор @receiver в signals защищает другие сигналы от дублирования сам по себе.
            dispatch_uid="users_sync_default_groups",
        )

        # Для JWT токенов: настройка отображения приложения и моделей JWT токенов в админ-панели
        from users.jwt_admin import customize_jwt_models

        customize_jwt_models()
