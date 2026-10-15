from types import SimpleNamespace

import pytest
from allauth.account.signals import user_signed_up
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from users.services.cache import get_cached_user, get_user_cache_key


User = get_user_model()


@pytest.fixture
def mock_logger(mocker):
    """Мок логгера для проверки вызова логирования."""
    return mocker.patch("users.signals.logger.info")


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
class TestUserDeletionSignals:
    """Тесты сигналов удаления пользователя."""

    def test_delete_user_triggers_avatar_cleanup_task(
        self, user_factory, django_capture_on_commit_callbacks
    ):
        """Удаление пользователя запускает очистку файлов аватара."""
        user = user_factory()
        path = default_storage.save(
            f"avatars/{user.s3_storage_uuid}/avatar.png", ContentFile(b"avatar")
        )

        with django_capture_on_commit_callbacks(execute=True):
            user.delete()

        assert not default_storage.exists(path)

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

    def test_user_cache_invalidation_on_update(
        self, user_factory, django_capture_on_commit_callbacks
    ):
        """
        При обновлении пользователя, кроме полей из USER_CACHE_IGNORED_FIELDS (например, пароля) с
        использованием .save(update_fields=[...]), удаляется кеш объекта пользователя.
        """
        user = user_factory()
        get_cached_user(user.username)
        assert cache.get(get_user_cache_key(user.username)) is not None

        # Кеш сбрасывается
        with django_capture_on_commit_callbacks(execute=True):
            user.first_name = "Ivan"
            user.save()

        assert cache.get(get_user_cache_key(user.username)) is None

        get_cached_user(user.username)

        # При обновлении пароля кеш не сбрасывается
        with django_capture_on_commit_callbacks(execute=True):
            user.set_password("NewStrongPassword123")
            user.save(update_fields=["password"])

        assert cache.get(get_user_cache_key(user.username)) is not None

    def test_username_change_invalidates_old_key(
        self, user_factory, django_capture_on_commit_callbacks
    ):
        """При обновлении username пользователя кеш по старому username сбрасывается."""
        user = user_factory(username="old_name")
        get_cached_user(username="old_name")

        with django_capture_on_commit_callbacks(execute=True):
            user.username = "new_name"
            user.save()

        assert cache.get(get_user_cache_key(username="old_name")) is None

    def test_user_cache_invalidation_on_delete(
        self, user_factory, django_capture_on_commit_callbacks
    ):
        """
        При удалении пользователя удаляется кеш объекта пользователя.
        """
        user = user_factory()
        get_cached_user(user.username)

        with django_capture_on_commit_callbacks(execute=True):
            user.delete()

        assert cache.get(get_user_cache_key(user.username)) is None
