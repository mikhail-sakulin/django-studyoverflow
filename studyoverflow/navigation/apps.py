from django.apps import AppConfig, apps
from django.db.models.signals import post_migrate


class NavigationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "navigation"

    def ready(self):
        """Выполняется после загрузки приложений."""
        # Кастомные схемы аутентификации, импорт для автоматической регистрации в Swagger
        import navigation.api.swagger_extensions  # noqa: F401

        # Регистрация обработчиков сигналов после загрузки приложения.
        from navigation import signals  # noqa: F401

        # AppConfig приложения django.contrib.sites
        sites_config = apps.get_app_config("sites")

        post_migrate.connect(
            signals.sync_site_domain,
            sender=sites_config,
            dispatch_uid="sync_site_domain",
        )
