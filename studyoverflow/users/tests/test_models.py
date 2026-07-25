import pytest
from django.urls import reverse
from users.models import User


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
    """Тестирование логики запуска Celery задач при работе с полями avatar."""

    @pytest.fixture(autouse=True)
    def mock_on_commit(self, mocker):
        """Фикстура заставляет transaction.on_commit выполнять колбэк немедленно."""
        # Celery задачи создаются через transaction.on_commit(lambda: ...),
        # мок для transaction.on_commit с данным side_effect заставляет запускать celery задачи
        # сразу же. Если их замокать тоже, то можно отслеживать вызов нужных задач.
        #
        # В func передается lamba: ..., которая передана в on_commit.
        #
        # При тестировании с @pytest.mark.django_db (или с TestCase) транзакция откатывается
        # после тестов, а не завершается, поэтому при реальном transaction.on_commit
        # задача никогда бы не создалась.
        return mocker.patch("users.models.transaction.on_commit", side_effect=lambda func: func())

    @pytest.fixture(autouse=True)
    def mock_handle_notification_user_created(self, mocker):
        # Мокается сервис создания уведомления, который вызовется при создании пользователя.
        #
        # Из-за фикстуры mock_on_commit celery задачи выполняются сразу, при создании пользователя
        # срабатывает сигнал, который вызывает создание приветственного уведомления, на это
        # срабатывает сигнал создания уведомления для обновления счетчика уведомлений у
        # пользователя (сигнал создает таску), где задействован уже Redis,
        # при отсутствии которого в тесте будет ошибка.
        #
        # В других тестах, где создается пользователь, все нормально, поскольку
        # не мокается transaction.on_commit.
        mocker.patch("notifications.signals.handle_notification_user_created")

    def test_creation_with_custom_avatar_triggers_celery(self, user_factory, mocker):
        """При создании пользователя с кастомным аватаром запускается задача генерации миниатюр."""
        mock_task = mocker.patch("users.tasks.generate_and_save_avatars_small.delay")

        user_factory(avatar="avatars/5/custom.jpg")

        mock_task.assert_called_once()

    def test_update_avatar_triggers_celery_chain(self, user_factory, mocker):
        """При обновлении аватара запускается цепочка (chain) Celery задач."""
        # Создается пользователь без запуска celery задачи
        mocker.patch("users.tasks.generate_and_save_avatars_small.delay")
        user = user_factory(avatar="avatars/5/old.jpg")

        mocker.patch(
            "users.models.get_old_avatar_names",
            return_value=("avatars/5/old.jpg", ["avatars/5/old_small.jpg"]),
        )
        # Мокается цепочка celery задач
        mock_chain = mocker.patch("users.models.chain")

        user.avatar = "avatars/5/new.jpg"
        user.save()

        mock_chain.assert_called_once()
        # Проверка, что цепочка задач запущена и отправлена в брокер сообщений
        # на выполнение (аналог .delay()) (при тестировании задачи выполняются сразу, брокера нет)
        mock_chain.return_value.apply_async.assert_called_once()

    def test_delete_avatar_resets_to_default_and_triggers_delete_task(self, user_factory, mocker):
        """
        Удаление аватара сбрасывает поля на дефолтные и запускает Celery задачу
        удаления старых файлов.
        """
        mocker.patch("users.tasks.generate_and_save_avatars_small.delay")
        user = user_factory(
            avatar="avatars/5/custom.jpg", avatar_small_size1="avatars/5/custom_small1.jpg"
        )

        mocker.patch(
            "users.models.get_old_avatar_names",
            return_value=(
                "avatars/5/custom.jpg",
                [
                    "avatars/5/custom.jpg",
                    "avatars/5/custom_small1.jpg",
                ],
            ),
        )
        mock_delete_task = mocker.patch("users.tasks.delete_old_avatars_from_s3_storage.delay")

        user.avatar = None
        user.save()

        assert user.avatar.name == User.DEFAULT_AVATAR_FILENAME
        assert user.avatar_small_size1.name == User.DEFAULT_AVATAR_SMALL_SIZE1_FILENAME
        mock_delete_task.assert_called_once_with(
            user.pk,
            [
                "avatars/5/custom.jpg",
                "avatars/5/custom_small1.jpg",
            ],
        )

    def test_save_without_avatar_change_does_not_trigger_celery(self, user_factory, mocker):
        """Сохранение профиля без изменения аватара не вызывает задачи Celery."""
        mocker.patch("users.tasks.generate_and_save_avatars_small.delay")
        user = user_factory(avatar="avatars/custom.jpg")

        # Моки Celery задач
        mock_chain = mocker.patch("users.models.chain")
        mock_delete_task = mocker.patch("users.tasks.delete_old_avatars_from_s3_storage.delay")
        mock_generate_task = mocker.patch("users.tasks.generate_and_save_avatars_small.delay")

        user.first_name = "Иван"
        user.save()

        mock_chain.assert_not_called()
        mock_delete_task.assert_not_called()
        mock_generate_task.assert_not_called()
