from types import SimpleNamespace

import pytest
from allauth.account.signals import user_signed_up
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed


User = get_user_model()


@pytest.fixture
def mock_logger(mocker):
    """Мок логгера для проверки вызова логирования."""
    return mocker.patch("users.signals.logger.info")


@pytest.fixture(autouse=True)
def mock_transaction_on_commit(mocker):
    """
    Выполнение transaction.on_commit в тестах.

    Вместо данной фикстуры с моком в самих тестах можно использовать контекстный менеджер Django
    django.test.TestCase.captureOnCommitCallbacks, или же фикстуру
    django_capture_on_commit_callbacks из pytest-django. При текущем моке коллбеки будут
    вызываться сразу при их регистрации. При использовании контекстного менеджера заданные
    колбеки (созданные при отработке кода внутри блока with) будут вызываться только после
    выхода из блока with, имитируя коммит транзакции.

    Пример использования контекстного менеджера внутри теста:

    with django_capture_on_commit_callbacks(execute=True) as callbacks:
        func()

    При execute=True коллбеки вызовутся после выхода из блока with.

    При использовании контекстного менеджера у теста должен быть декоратор @pytest.mark.django_db,
    так как настоящий transaction.on_commit проверяет состояние транзакции через соединение с БД,
    даже если тест сам не работает с БД.
    """
    return mocker.patch("django.db.transaction.on_commit", side_effect=lambda func: func())


@pytest.fixture(autouse=True)
def mock_celery_task_create_notification(mocker):
    """
    Поскольку мокается transaction.on_commit, то после создания объектов (пользователя, поста,
    комментария) через сигналы и слой сервисов уведомлений запускается celery-задача,
    которая использует redis, поэтому она мокается.
    """
    mocker.patch("notifications.services.notification_handlers.create_notification.delay")


@pytest.mark.django_db
class TestUserDeletionSignals:
    """Тесты сигналов удаления пользователя."""

    def test_delete_user_triggers_avatar_cleanup_task(self, user_factory, mocker):
        """Удаление пользователя запускает очистку файлов аватара."""
        user = user_factory()

        mock_task = mocker.patch("users.signals.delete_all_avatars_files_task.delay")

        user.delete()

        mock_task.assert_called_once_with(str(user.s3_storage_uuid))

    def test_delete_user_writes_log(self, user_factory, mock_logger):
        """Удаление пользователя записывает событие в лог."""
        user = user_factory()

        user.delete()

        mock_logger.assert_called_once()


class TestAuthSignals:
    """Тесты сигналов авторизации."""

    def test_user_login_writes_log(self, mock_logger, mocker):
        """Успешный вход пользователя записывает лог."""
        user = SimpleNamespace(
            username="user",
            pk=1,
            email="test@example.com",
            is_social=False,
            save=mocker.Mock(),
        )

        user_logged_in.send(sender=User, request=None, user=user)

        mock_logger.assert_called_once()

    def test_user_logout_removes_online_status(self, mocker, mock_logger):
        """Выход пользователя удаляет статус online."""
        user = SimpleNamespace(
            username="user",
            pk=5,
            email="test@example.com",
            is_social=False,
        )

        mock_remove_online = mocker.patch("users.signals.remove_user_offline")

        user_logged_out.send(sender=User, request=None, user=user)

        mock_remove_online.assert_called_once_with(5)

        mock_logger.assert_called_once()


class TestSignupSignal:
    """Тесты регистрации пользователя."""

    def test_user_signup_writes_log(self, mock_logger):
        """Регистрация пользователя записывает лог."""
        user = SimpleNamespace(username="user", pk=1, email="test@example.com", is_social=False)

        user_signed_up.send(sender=None, request=None, user=user)

        mock_logger.assert_called_once()


class TestLoginFailedSignal:
    """Тесты неудачного входа."""

    def test_failed_login_writes_log(self, mock_logger):
        """Неудачная попытка входа записывает лог."""
        user_login_failed.send(sender=User, credentials={"username": "test"}, request=None)

        mock_logger.assert_called_once()


@pytest.mark.django_db
class TestUserObjectCacheSignals:

    def test_user_cache_invalidation_on_update(self, user_factory, mocker):
        """
        При обновлении пользователя, кроме пароля, вызывается сервис удаления кеша
        объекта пользователя.
        """
        mock_delete_cache = mocker.patch("users.signals.delete_cache_user")

        # 1) Создание пользователя — кеш не сбрасывается
        user = user_factory()
        mock_delete_cache.assert_not_called()

        # 2) Обновление пользователя — кеш сбрасывается
        user.first_name = "new_username"
        user.save()
        mock_delete_cache.assert_called_once_with(user.username)

    def test_user_cache_invalidation_on_delete(self, user_factory, mocker):
        """
        При удалении пользователя вызывается сервис удаления кеша
        объекта пользователя.
        """
        mock_delete_cache = mocker.patch("users.signals.delete_cache_user")

        # 1) Создание пользователя — кеш не сбрасывается
        user = user_factory()
        mock_delete_cache.assert_not_called()

        # 3) Удаление пользователя — кеш сбрасывается
        mock_delete_cache.reset_mock()
        username = user.username
        user.delete()
        mock_delete_cache.assert_called_once_with(username)
