from django.apps import AppConfig


class PostsConfig(AppConfig):
    verbose_name = "Посты (posts)"
    default_auto_field = "django.db.models.BigAutoField"
    name = "posts"

    def ready(self):
        """Регистрация обработчиков сигналов после загрузки приложения."""
        import posts.signals  # noqa: F401
