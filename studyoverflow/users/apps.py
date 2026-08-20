from django.apps import AppConfig
from django.db.models.signals import post_migrate


class UsersConfig(AppConfig):
    verbose_name = "Пользователи (users)"
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"

    def ready(self):
        """
        Выполняется после загрузки приложений, но до выполнения миграций.
        """
        # Регистрация обработчиков сигналов после загрузки приложения.
        from users import signals  # noqa: F401

        # Ручная регистрация обработчиков сигналов.
        # Сигнал post_migrate срабатывает после выполнения всех миграций приложения.
        post_migrate.connect(
            signals.sync_default_groups,
            # Сигнал срабатывает только после выполнения миграций приложения users,
            # self - экземпляр UsersConfig, конфигурационный объект приложения users.
            # Без self обработчик сигнала вызывался бы после миграций любого приложения.
            sender=self,
            # ID обработчика сигнала для этого приложения, гарантирует, что функция будет привязана
            # к сигналу post_migrate ровно один раз, чтобы, если вдруг будет вторая миграция,
            # сигнал не отработал на событие дважды.
            #
            # Декоратор @receiver в signals защищает автоматически
            # обработчики сигналов от дублирования.
            dispatch_uid="users_sync_default_groups",
        )

        # Для JWT токенов: настройка отображения приложения и моделей JWT токенов в админ-панели
        from users.jwt_admin import customize_jwt_models

        customize_jwt_models()
