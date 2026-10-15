import io
import uuid
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils import timezone
from PIL import Image

from users.services.online import set_user_online
from users.tasks import (
    clear_expired_sessions,
    delete_all_avatars_files_task,
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


def make_png_bytes(size: tuple[int, int] = (300, 300)) -> bytes:
    """Возвращает содержимое PNG-файла заданного размера."""
    buffer = io.BytesIO()
    Image.new("RGB", size, "red").save(buffer, format="PNG")
    return buffer.getvalue()


def put_file(path: str, content: bytes | None = None) -> str:
    """
    Сохраняет файл в default_storage (InMemoryStorage в тестах) и возвращает его имя (путь
    файла в хранилище).
    """
    return default_storage.save(path, ContentFile(content or make_png_bytes()))


@pytest.mark.django_db
class TestAvatarTasks:
    """Тестирование Celery задач обработки и удаления аватаров."""

    def test_generate_avatars_user_not_found(self, mock_logger):
        """Логирует предупреждение, если пользователь не найден."""
        generate_and_save_avatars_small(user_pk=1000)
        mock_logger.warning.assert_called_once()

    def test_generate_and_save_avatars_success(self, user_factory):
        """Генерирует и сохраняет уменьшенные версии аватара в хранилище."""
        s3_storage_uuid = uuid.uuid4()
        avatar = put_file(f"avatars/{s3_storage_uuid}/avatar.png", make_png_bytes((400, 400)))
        user = user_factory(avatar=avatar, s3_storage_uuid=s3_storage_uuid)

        generate_and_save_avatars_small(user.pk)

        user.refresh_from_db()
        # Миниатюры созданы и лежат в хранилище
        avatar_small_names = [
            getattr(user, field_name).name for field_name in UserModel.get_small_avatar_fields()
        ]
        assert all(default_storage.exists(name) for name in avatar_small_names)

    def test_delete_old_avatars_with_explicit_list(self, user_factory):
        """Удаляет из хранилища ("директории" пользователя) файлы по переданному списку."""
        user = user_factory()
        # Директория с аватарками пользователя в хранилище
        folder = f"avatars/{user.s3_storage_uuid}"
        # Старые аватары в хранилище
        old_1 = put_file(f"{folder}/old1.png")
        old_1_small = put_file(f"{folder}/old_1_small.png")
        # Новый аватар в хранилище
        new_avatar = put_file(f"{folder}/new_avatar.png")

        delete_old_avatars_from_s3_storage(user.pk, [old_1, old_1_small])

        # Старые аватары удалены, новый аватар остался
        assert not default_storage.exists(old_1)
        assert not default_storage.exists(old_1_small)
        assert default_storage.exists(new_avatar)

    def test_delete_old_avatars_auto_detect(self, user_factory):
        """Определяет и удаляет лишние файлы из хранилища ("директории" пользователя)."""
        s3_storage_uuid = uuid.uuid4()
        # Директория с аватарками пользователя в хранилище
        folder = f"avatars/{s3_storage_uuid}"

        # Старые аватары в хранилище
        old_1 = put_file(f"{folder}/old1.png")
        old_1_small = put_file(f"{folder}/old_1_small.png")

        # Новый аватар в хранилище
        new_avatar = put_file(f"{folder}/new_avatar.png")
        user = user_factory(s3_storage_uuid=s3_storage_uuid, avatar=new_avatar)

        # Если список старых файлов не передан, то задача сама определяет и удаляет старые файлы
        delete_old_avatars_from_s3_storage(user.pk)

        # Старые аватары удалены, новый аватар остался
        assert not default_storage.exists(old_1)
        assert not default_storage.exists(old_1_small)
        assert default_storage.exists(new_avatar)

    def test_delete_files_from_storage_task(self):
        """
        Удаляет все файлы аватарок из "директории" пользователя из хранилища, файлы
        других пользователей не затрагиваются.
        """
        folder_uuid = str(uuid.uuid4())
        file_1 = put_file(f"avatars/{folder_uuid}/file1.png")
        file_2 = put_file(f"avatars/{folder_uuid}/file2.png")
        foreign = put_file(f"avatars/{uuid.uuid4()}/file.png")

        delete_all_avatars_files_task(folder_uuid=folder_uuid)

        assert not default_storage.exists(file_1)
        assert not default_storage.exists(file_2)
        assert default_storage.exists(foreign)


@pytest.mark.django_db
class TestSyncTasks:

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Очищает кеш до и после каждого теста."""
        cache.clear()
        yield
        cache.clear()

    def test_sync_online_users(self, user_factory, mocker):
        """Обновляет last_seen для онлайн-пользователей."""
        initial_last_seen = timezone.now()
        online_user = user_factory(last_seen=initial_last_seen)
        offline_user = user_factory(last_seen=initial_last_seen)
        set_user_online(online_user.pk)

        next_last_seen = initial_last_seen + timedelta(minutes=5)
        mocker.patch("django.utils.timezone.now", return_value=next_last_seen)

        sync_online_users_to_db()

        online_user.refresh_from_db()
        offline_user.refresh_from_db()
        assert online_user.last_seen == next_last_seen
        assert offline_user.last_seen == initial_last_seen

    def test_sync_counters(self, user_factory, post_factory, comment_factory, like_factory):
        """Синхронизирует счётчики постов, комментариев и репутации."""
        author, commenter, liker, viewer = (user_factory() for _ in range(4))

        post_1, _post_2 = post_factory.create_batch(2, author=author)
        comment = comment_factory(post=post_1, author=commenter)
        like_factory(user=liker, content_object=post_1)
        like_factory(user=liker, content_object=comment)

        # Счетчики задаются недействительные через update, чтобы сигналы не сработали
        UserModel.objects.update(posts_count=999, comments_count=999, reputation=999)

        sync_user_activity_counters(batch_size=2)

        for user in (author, commenter, liker, viewer):
            user.refresh_from_db()

        assert (author.posts_count, author.comments_count, author.reputation) == (2, 0, 1)
        assert (commenter.posts_count, commenter.comments_count, commenter.reputation) == (0, 1, 1)
        assert (liker.posts_count, liker.comments_count, liker.reputation) == (0, 0, 0)
        assert (viewer.posts_count, viewer.comments_count, viewer.reputation) == (0, 0, 0)


@pytest.mark.django_db
class TestDownloadAvatar:
    """Тестирование скачивания аватарок при регистрации через соцсети."""

    @pytest.fixture
    def mock_requests(self, mocker):
        """Мок requests.get, возвращается PNG 200x200."""
        response = mocker.Mock()
        response.content = make_png_bytes((200, 200))
        response.raise_for_status.return_value = None
        return mocker.patch("users.tasks.requests.get", return_value=response)

    def test_successful_download_and_save(self, user_factory, mock_requests):
        """Скачивает, валидирует и сохраняет аватар из соцсети."""
        user = user_factory()

        download_and_set_avatar(user.pk, "http://example.com/pic.jpg")

        mock_requests.assert_called_once_with("http://example.com/pic.jpg", timeout=5)

        user.refresh_from_db()

        assert user.avatar.name != UserModel.DEFAULT_AVATAR_FILENAME
        assert default_storage.exists(user.avatar.name)
        with default_storage.open(user.avatar.name) as file:
            assert file.read() == mock_requests.return_value.content

    def test_skip_if_avatar_exists(self, user_factory, mock_requests):
        """Пропускает скачивание, если аватар, отличный от стандартного, уже установлен."""
        custom = put_file(f"avatars/{uuid.uuid4()}/avatar.png")
        user = user_factory(avatar=custom)

        download_and_set_avatar(user.pk, "http://example.com/avatar.jpg")

        mock_requests.assert_not_called()
        user.refresh_from_db()
        assert user.avatar.name == custom
        assert default_storage.exists(user.avatar.name)

    def test_validation_error_logging(self, user_factory, mock_requests, mock_logger):
        """Проверяет отработку валидации аватара при невалидном аватаре."""
        mock_requests.return_value.content = make_png_bytes((50, 50))
        user = user_factory()

        download_and_set_avatar(user.pk, "http://example.com/pic.jpg")

        mock_logger.info.assert_called_once()
        extra = mock_logger.info.call_args.kwargs["extra"]
        assert extra["event_type"] == "download_and_set_avatar_validation_error"

        user.refresh_from_db()
        assert user.avatar.name == UserModel.DEFAULT_AVATAR_FILENAME


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
