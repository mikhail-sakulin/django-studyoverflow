from django.apps import AppConfig
from django.db.models.fields import CharField, TextField


class PostsConfig(AppConfig):
    verbose_name = "Посты (posts)"
    default_auto_field = "django.db.models.BigAutoField"
    name = "posts"

    def ready(self):
        # Регистрация обработчиков сигналов после загрузки приложения
        import posts.signals  # noqa: F401

        # Кастомный лукап
        from posts.lookups import IContainsILike  # noqa: F401

        # Регистрация кастомного лукапа для строк и текстовых полей
        CharField.register_lookup(IContainsILike)
        TextField.register_lookup(IContainsILike)
