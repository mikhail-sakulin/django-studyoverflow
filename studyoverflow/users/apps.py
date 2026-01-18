from django.apps import AppConfig


class UsersConfig(AppConfig):
    verbose_name = "Пользователи (users)"
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"

    def ready(self):
        import users.signals  # noqa: F401
