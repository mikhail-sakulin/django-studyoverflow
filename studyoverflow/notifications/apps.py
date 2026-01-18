from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    verbose_name = "Уведомления (notifications)"
    default_auto_field = "django.db.models.BigAutoField"
    name = "notifications"

    def ready(self):
        import notifications.signals  # noqa: F401
