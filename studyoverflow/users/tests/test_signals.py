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


@pytest.mark.django_db
class TestUserDeletionSignals:
    """Тесты сигналов удаления пользователя."""

    @pytest.fixture(autouse=True)
    def mock_on_commit(self, mocker):
        """Выполнение transaction.on_commit в тестах."""
        return mocker.patch("django.db.transaction.on_commit", side_effect=lambda func: func())

    @pytest.fixture(autouse=True)
    def mock_handle_notification_user_created(self, mocker):
        # Мокается сервис создания уведомления, который вызовется при создании пользователя.
        #
        # В других тестах, где создается пользователь, все нормально, поскольку
        # не мокается transaction.on_commit.
        mocker.patch("notifications.signals.handle_notification_user_created")

    def test_delete_user_triggers_avatar_cleanup_task(self, user_factory, mocker, mock_on_commit):
        """Удаление пользователя запускает очистку файлов аватара."""
        user = user_factory()

        mocker.patch(
            "users.signals.get_user_avatar_paths_list", return_value=["avatars/5/test.jpg"]
        )
        mock_task = mocker.patch("users.signals.delete_files_from_storage_task.delay")

        user.delete()

        mock_task.assert_called_once_with(["avatars/5/test.jpg"])

    def test_delete_user_without_avatar_does_not_trigger_cleanup(
        self, user_factory, mocker, mock_on_commit
    ):
        """Удаление пользователя без файлов аватара не запускает очистку."""
        user = user_factory()

        mocker.patch("users.signals.get_user_avatar_paths_list", return_value=[])
        mock_task = mocker.patch("users.signals.delete_files_from_storage_task.delay")

        user.delete()

        mock_task.assert_not_called()

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
