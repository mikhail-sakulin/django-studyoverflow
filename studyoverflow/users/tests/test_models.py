import io
import uuid

import pytest
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.urls import reverse
from PIL import Image

from users.models import User


def put_avatar(folder_uuid: str, name: str = "avatar.png") -> str:
    """
    Сохраняет в default_storage (InMemoryStorage для тестов) тестовое PNG-изображение 300x300
    по пути avatars/<folder_uuid>/<name> и возвращает имя файла в хранилище.
    """
    buffer = io.BytesIO()
    Image.new("RGB", (300, 300), "red").save(buffer, format="PNG")
    return default_storage.save(f"avatars/{folder_uuid}/{name}", ContentFile(buffer.getvalue()))


def small_avatar_names(user: User) -> list[str]:
    """Возвращает пути к файлам миниатюр аватара пользователя в хранилище."""
    return [getattr(user, field_name).name for field_name in User.get_small_avatar_fields()]


@pytest.mark.django_db
class TestCustomUserManager:
    def test_get_by_natural_key_username(self, user_factory):
        """Менеджер находит пользователя по username."""
        user = user_factory(username="test_user")
        assert User.objects.get_by_natural_key("test_user") == user

    def test_get_by_natural_key_email_case_insensitive(self, user_factory):
        """Менеджер находит пользователя по email без учета регистра."""
        user = user_factory(email="test@example.com")
        assert User.objects.get_by_natural_key("TEST@EXAMPLE.COM") == user


@pytest.mark.django_db
class TestUserModelSaveLogic:
    def test_email_is_lowercased_on_save(self, user_factory):
        """При сохранении модели email приводится к нижнему регистру."""
        user = user_factory(email="UPPERCASE@EXAMPLE.COM")
        assert user.email == "uppercase@example.com"

    def test_role_syncs_with_staff_flags(self, user_factory):
        """Проверяет установку флагов is_staff и is_superuser на основе роли."""
        user = user_factory(role=User.Role.ADMIN)
        assert user.is_staff is True
        assert user.is_superuser is True

        user.role = User.Role.MODERATOR
        user.save()
        assert user.is_staff is True
        assert user.is_superuser is False

        user.role = User.Role.USER
        user.save()
        assert user.is_staff is False
        assert user.is_superuser is False

    def test_role_if_created_superuser(self, user_factory):
        """Если создается superuser, то автоматически задается роль администратора."""
        user = user_factory(is_superuser=True)
        assert user.role == User.Role.ADMIN
        assert user.is_staff is True
        assert user.is_superuser is True

    def test_role_syncs_with_groups(self, user_factory):
        """Смена роли добавляет или удаляет пользователя из соответствующих групп."""
        user = user_factory(role=User.Role.MODERATOR)

        # Выбираются имена групп, в которых состоит пользователь, и сохраняются в set,
        # flat=True задает формат возвращаемого значения как список значений, а не кортежей
        group_names = set(user.groups.values_list("name", flat=True))
        assert group_names == {"Moderators", "StaffViewers"}

        # Понижение роли
        user.role = User.Role.USER
        user.save()

        # При понижении роли пользователь должен удалиться из групп
        assert not user.groups.exists()

    def test_role_syncs_with_staff_viewer_group(self, user_factory):
        """При роли STAFF_VIEWER назначает только группа StaffViewers."""
        user = user_factory(role=User.Role.STAFF_VIEWER)

        group_names = set(user.groups.values_list("name", flat=True))
        assert group_names == {"StaffViewers"}


@pytest.mark.django_db
class TestUserModelMethods:
    def test_get_absolute_url(self, user_factory):
        """Метод возвращает правильный URL профиля."""
        user = user_factory(username="test_user")
        expected_url = reverse("users:profile", kwargs={"username": "test_user"})
        assert user.get_absolute_url() == expected_url

    def test_get_avatar_small_url_returns_main_if_small_missing(self, user_factory):
        """Если миниатюра отсутствует, метод возвращает URL основного аватара."""
        user = user_factory(avatar="avatars/5/main.jpg", avatar_small_size1="")
        assert user.get_avatar_small_url("size1") == user.avatar.url


@pytest.mark.django_db
class TestUserModelAvatarCeleryTasks:
    """
    Тестирование логики обработки аватара при работе с моделью пользователя.

    В настройках тестирования задано CELERY_TASK_ALWAYS_EAGER = True, поэтому Celery-задачи в
    тестах выполняются синхронно (сразу), но только после коммита транзакции — в тестах
    нужно эмулировать через django_capture_on_commit_callbacks.
    """

    def test_creation_with_custom_avatar_generates_thumbnails(
        self, user_factory, django_capture_on_commit_callbacks
    ):
        """
        При создании пользователя с кастомным аватаром после коммита транзакции
        генерируются все миниатюры, их файлы появляются в хранилище.
        """
        avatar = put_avatar(str(uuid.uuid4()))

        with django_capture_on_commit_callbacks(execute=True):
            user = user_factory(avatar=avatar)

        user.refresh_from_db()
        avatar_small_names = small_avatar_names(user)

        # Аватар и миниатюры созданы и лежат в хранилище
        assert default_storage.exists(user.avatar.name)
        assert all(default_storage.exists(name) for name in avatar_small_names)

    def test_replacing_avatar_generates_new_thumbnails_and_deletes_old_files(
        self, user_factory, django_capture_on_commit_callbacks
    ):
        """
        При замене аватара генерируются новые миниатюры, файлы предыдущего аватара
        удаляются из хранилища.
        """
        folder = str(uuid.uuid4())
        old = put_avatar(folder, "old.png")

        # Создание пользователя с кастомным аватаром, миниатюры создаются
        with django_capture_on_commit_callbacks(execute=True):
            user = user_factory(avatar=old)

        user.refresh_from_db()
        assert default_storage.exists(user.avatar.name)
        old_small_names = small_avatar_names(user)
        assert all(default_storage.exists(name) for name in old_small_names)

        new = put_avatar(folder, "new.png")

        # Обновление аватара и миниатюр
        with django_capture_on_commit_callbacks(execute=True):
            user.avatar = new
            user.save()

        user.refresh_from_db()
        new_small_names = small_avatar_names(user)

        # Проверка, что аватар и все миниатюры обновились (имена новые) и их файлы лежат в хранилище
        assert user.avatar.name == new
        assert not (set(new_small_names) & set(old_small_names))
        assert default_storage.exists(user.avatar.name)
        assert all(default_storage.exists(name) for name in new_small_names)

        # Старый аватар и его миниатюры удалены из хранилища
        assert not default_storage.exists(old)
        assert not any(default_storage.exists(name) for name in old_small_names)

    def test_resetting_avatar_restores_defaults_and_deletes_files(
        self, user_factory, django_capture_on_commit_callbacks
    ):
        """
        Удаление аватара сбрасывает аватар и миниатюры на дефолтные значения
        и удаляет старый файл из хранилища.
        """
        old = put_avatar(str(uuid.uuid4()))

        # Создание пользователя с кастомным аватаром, миниатюры создаются
        with django_capture_on_commit_callbacks(execute=True):
            user = user_factory(avatar=old)

        # Аватар и его миниатюры сохранены в хранилище
        user.refresh_from_db()
        old_small_names = small_avatar_names(user)
        assert default_storage.exists(user.avatar.name)
        assert all(default_storage.exists(name) for name in old_small_names)

        # Удаление аватара задает стандартные значения для него и миниатюр, старые файлы
        # удаляются из хранилища
        with django_capture_on_commit_callbacks(execute=True):
            user.avatar = None
            user.save()

        user.refresh_from_db()

        # После сброса аватара заданы стандартные значения, старые файлы удалены из хранилища
        assert user.avatar.name == User.DEFAULT_AVATAR_FILENAME
        assert user.avatar_small_size1.name == User.DEFAULT_AVATAR_SMALL_SIZE1_FILENAME
        assert user.avatar_small_size2.name == User.DEFAULT_AVATAR_SMALL_SIZE2_FILENAME
        assert user.avatar_small_size3.name == User.DEFAULT_AVATAR_SMALL_SIZE3_FILENAME

        assert not default_storage.exists(old)
        assert not any(default_storage.exists(name) for name in old_small_names)

    def test_save_without_avatar_change_does_not_touch_files(
        self, user_factory, django_capture_on_commit_callbacks
    ):
        """
        Сохранение профиля без изменения аватара не затрагивает файлы в хранилище
        и не запускает генерацию миниатюр.
        """
        avatar = put_avatar(str(uuid.uuid4()))

        with django_capture_on_commit_callbacks(execute=True):
            user = user_factory(avatar=avatar)

        user.refresh_from_db()
        old_small_names = small_avatar_names(user)
        assert default_storage.exists(user.avatar.name)
        assert all(default_storage.exists(name) for name in old_small_names)

        with django_capture_on_commit_callbacks(execute=True):
            user.first_name = "Иван"
            user.save()

        # После обновления пользователя без изменения аватара, аватар и его миниатюры не меняются
        user.refresh_from_db()
        new_small_names = small_avatar_names(user)

        assert user.avatar.name == avatar
        assert default_storage.exists(avatar)
        # миниатюры не обновлялись
        assert old_small_names == new_small_names
        assert all(default_storage.exists(name) for name in new_small_names)
