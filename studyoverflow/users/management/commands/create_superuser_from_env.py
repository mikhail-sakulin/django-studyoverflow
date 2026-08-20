import os
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    """
    Django management command для создания суперпользователя из переменных окружения.
    """

    # Документация команды, выводимая при python manage.py create_superuser_from_env --help
    help = (  # noqa: A003
        "Создаёт суперпользователя из переменных окружения, если он еще не был создан."
    )

    def handle(self, *args, **options):
        """
        Метод, вызываемый при выполнении команды.

        Считывает обязательные переменные окружения для создания суперпользователя и создает его.
        При отсутствии обязательных параметров команда завершается с CommandError, а
        при существующем пользователе завершается без изменения БД.

        Настройки settings выполняются при инициализации Django до загрузки приложений и до
        выполнения самой команды, поэтому переменные окружения для команды уже будут
        загружены при выполнении settings.
        """
        User = get_user_model()

        username = os.getenv("DJANGO_SUPERUSER_USERNAME")
        email = os.getenv("DJANGO_SUPERUSER_EMAIL")
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD")

        if not username:
            raise CommandError("DJANGO_SUPERUSER_USERNAME не задан.")

        if not email:
            raise CommandError("DJANGO_SUPERUSER_EMAIL не задан.")

        if not password:
            raise CommandError("DJANGO_SUPERUSER_PASSWORD не задан.")

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                # Метод .style.SUCCESS выводит зеленый текст.
                self.style.SUCCESS(f"Суперпользователь '{username}' уже существует.")
            )
            return

        # Мокается создание Celery задачи для создания приветственного уведомления о регистрации
        # пользователя, чтобы команду можно было выполнять без поднятия
        # брокера сообщений для Celery.
        with patch("notifications.services.notification_handlers.create_notification.delay"):
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
            )

            self.stdout.write(self.style.SUCCESS(f"Суперпользователь '{username}' создан."))
