from django.apps import AppConfig


class PostsConfig(AppConfig):
    verbose_name = "Посты (posts)"
    default_auto_field = "django.db.models.BigAutoField"
    name = "posts"

    def ready(self):
        import posts.signals  # noqa: F401
