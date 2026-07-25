from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from users.tasks import (
    clear_expired_sessions,
    delete_files_from_storage_task,
    delete_old_avatars_from_s3_storage,
    download_and_set_avatar,
    flush_expired_jwt_tokens,
    generate_and_save_avatars_small,
    send_password_reset_email_task,
    sync_online_users_to_db,
    sync_user_activity_counters,
)


UserModel = get_user_model()


@pytest.fixture
def mock_logger(mocker):
    return mocker.patch("users.tasks.logger")


@pytest.mark.django_db
class TestAvatarTasks:
    """Тестирование Celery задач обработки и удаления аватаров."""

    def test_generate_avatars_user_not_found(self, mock_logger):
        """Логирует предупреждение, если пользователь не найден."""
        generate_and_save_avatars_small(user_pk=1000)
        mock_logger.warning.assert_called_once()

    def test_generate_and_save_avatars_success(self, user_factory, mocker):
        """Генерирует и сохраняет уменьшенные версии аватара."""
        user = user_factory()

        mocker.patch(
            "users.tasks.generate_avatar_small",
            side_effect=["avatar_1.jpg", "avatar_2.jpg"],
        )
        mocker.patch.object(
            UserModel,
            "get_small_avatar_fields",
            return_value=["avatar_small_size1", "avatar_small_size2"],
        )

        generate_and_save_avatars_small(user.pk)
        user.refresh_from_db()
        assert user.avatar_small_size1 == "avatar_1.jpg"
        assert user.avatar_small_size2 == "avatar_2.jpg"

    def test_delete_old_avatars_with_explicit_list(self, user_factory, mocker):
        """Удаляет файлы по переданному списку."""
        user = user_factory()
        mock_delete = mocker.patch("users.tasks.delete_old_avatar_names")
        delete_old_avatars_from_s3_storage(user.pk, ["old1.jpg", "old2.jpg"])
        mock_delete.assert_called_once_with(["old1.jpg", "old2.jpg"])

    def test_delete_old_avatars_auto_detect(self, user_factory, mocker):
        """Определяет и удаляет лишние файлы из хранилища."""
        user = user_factory()
        user.avatar = f"avatars/{user.pk}/main.jpg"
        user.save()
        mocker.patch.object(UserModel, "get_small_avatar_fields", return_value=[])
        mocker.patch(
            "users.tasks.default_storage.listdir",
            return_value=([], ["main.jpg", "old.jpg"]),
        )
        mock_delete = mocker.patch("users.tasks.delete_old_avatar_names")
        delete_old_avatars_from_s3_storage(user.pk)
        mock_delete.assert_called_once_with([f"avatars/{user.pk}/old.jpg"])

    def test_delete_files_from_storage_task(self, mocker):
        """Вызывает удаление переданного списка файлов."""
        mock_delete = mocker.patch("users.tasks.delete_old_avatar_names")
        delete_files_from_storage_task(["file1.jpg", "file2.jpg"])
        mock_delete.assert_called_once_with(["file1.jpg", "file2.jpg"])


@pytest.mark.django_db
class TestSyncTasks:

    def test_sync_online_users(self, user_factory, mocker):
        """Обновляет last_seen для онлайн-пользователей."""
        initial_last_seen = timezone.now()
        user = user_factory(last_seen=initial_last_seen)

        next_last_seen = initial_last_seen + timedelta(minutes=5)
        mocker.patch("django.utils.timezone.now", return_value=next_last_seen)

        mocker.patch("users.tasks.get_cached_online_user_ids", return_value=[user.pk])
        sync_online_users_to_db()

        user.refresh_from_db()
        assert user.last_seen == next_last_seen

    def test_sync_counters(self, user_factory, mocker):
        """Синхронизирует счётчики постов, комментариев и репутации."""
        user = user_factory(posts_count=0, comments_count=0, reputation=0)
        mocker.patch(
            "users.tasks.get_counts_map",
            side_effect=[{user.pk: 10}, {user.pk: 5}],
        )
        mocker.patch("users.tasks.get_reputation_map", return_value={user.pk: 100})
        sync_user_activity_counters()
        user.refresh_from_db()
        assert user.posts_count == 10
        assert user.comments_count == 5
        assert user.reputation == 100


@pytest.mark.django_db
class TestDownloadAvatar:
    """Тестирование скачивания аватарок при регистрации через соцсети."""

    @pytest.fixture
    def mock_requests(self, mocker):
        response = mocker.Mock()
        response.content = b"fake_image_bytes"
        response.raise_for_status.return_value = None
        return mocker.patch("users.tasks.requests.get", return_value=response)

    def test_successful_download_and_save(self, user_factory, mocker, mock_requests):
        """Скачивает и сохраняет аватар из соцсети."""
        user = user_factory()
        mock_save = mocker.patch("django.db.models.fields.files.FieldFile.save")
        mocker.patch.object(user._meta.get_field("avatar"), "validators", [])

        download_and_set_avatar(user.pk, "http://example.com/pic.jpg")

        mock_requests.assert_called_once_with("http://example.com/pic.jpg", timeout=5)
        mock_save.assert_called_once()
        assert mock_save.call_args[0][0] == "social_avatar.jpg"

    def test_skip_if_avatar_exists(self, user_factory, mocker, mock_requests):
        """Пропускает скачивание, если аватар, отличный от стандартного, уже установлен."""
        user = user_factory(avatar="avatars/custom.jpg")

        mocker.patch.object(
            user._meta.get_field("avatar"), "get_default", return_value="default.jpg"
        )

        download_and_set_avatar(user.pk, "http://example.com/avatar.jpg")

        mock_requests.assert_not_called()

    def test_validation_error_logging(self, user_factory, mocker, mock_requests, mock_logger):
        """Логирует предупреждение при ошибке валидации аватара."""
        user = user_factory()

        def fake_validator(file):
            raise ValidationError("Invalid image")

        mocker.patch.object(user._meta.get_field("avatar"), "validators", [fake_validator])
        download_and_set_avatar(user.pk, "http://example.com/pic.jpg")
        mock_logger.info.assert_called_once()


class TestAuthAndManagementTasks:
    """Тестирование остальных Celery задач."""

    def test_send_password_reset_email_valid(self, mocker):
        """Отправляет письмо для сброса пароля при валидном email."""
        mocker.patch("users.tasks.PasswordResetForm.is_valid", return_value=True)
        mock_save = mocker.patch("users.tasks.PasswordResetForm.save")

        send_password_reset_email_task("test@mail.com", "example.com", True)

        mock_save.assert_called_once()

    def test_send_password_reset_email_invalid(self, mocker, mock_logger):
        """Логирует запрос при невалидном email."""
        mocker.patch("users.tasks.PasswordResetForm.is_valid", return_value=False)

        send_password_reset_email_task("bad@mail", "example.com", True)

        mock_logger.info.assert_called_once()

    def test_clear_expired_sessions(self, mocker):
        """Вызывает команду очистки истёкших сессий."""
        mock_call = mocker.patch("users.tasks.call_command")

        clear_expired_sessions()

        mock_call.assert_called_once_with("clearsessions")

    def test_flush_expired_jwt_tokens(self, mocker):
        """Вызывает команду очистки истёкших JWT-токенов."""
        mock_call = mocker.patch("users.tasks.call_command")

        flush_expired_jwt_tokens()

        mock_call.assert_called_once_with("flushexpiredtokens")
