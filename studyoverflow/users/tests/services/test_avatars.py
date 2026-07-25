import io
import uuid

import pytest
from botocore.exceptions import BotoCoreError
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from users.services import (
    avatar_upload_to,
    delete_old_avatar_names,
    generate_avatar_small,
    generate_default_avatar_in_different_sizes,
    generate_default_avatar_small,
    generate_new_filename_with_uuid,
    get_old_avatar_names,
    get_storage_path_to_avatar_with_ext,
    get_user_avatar_paths_list,
    save_img_in_storage,
    user_avatar_upload_path,
)


User = get_user_model()


@pytest.fixture
def mock_user(mocker):
    user = mocker.Mock()
    user.pk = 5
    user.username = "test_user"
    user.avatar.name = "avatars/5/avatar.png"

    # DEFAULT_AVATAR_FILENAME = "avatars/default_avatar.jpg"
    # DEFAULT_AVATAR_SMALL_SIZE1_FILENAME = "avatars/default_avatar_small_size1.jpg"
    # DEFAULT_AVATAR_SMALL_SIZE2_FILENAME = "avatars/default_avatar_small_size2.jpg"
    # DEFAULT_AVATAR_SMALL_SIZE3_FILENAME = "avatars/default_avatar_small_size3.jpg"
    # AVATAR_SMALL_SIZES = {
    #     "size1": (100, 100),
    #     "size2": (170, 170),
    #     "size3": (800, 800),
    # }
    user.DEFAULT_AVATAR_FILENAME = User.DEFAULT_AVATAR_FILENAME
    user.DEFAULT_AVATAR_SMALL_SIZE1_FILENAME = User.DEFAULT_AVATAR_SMALL_SIZE1_FILENAME
    user.DEFAULT_AVATAR_SMALL_SIZE2_FILENAME = User.DEFAULT_AVATAR_SMALL_SIZE2_FILENAME
    user.DEFAULT_AVATAR_SMALL_SIZE3_FILENAME = User.DEFAULT_AVATAR_SMALL_SIZE3_FILENAME
    user.AVATAR_SMALL_SIZES = User.AVATAR_SMALL_SIZES
    return user


class TestFilenamesAndPaths:
    """
    Тестирование путей и имен файлов.
    """

    @pytest.mark.parametrize("original, expected_ext", [("photo.JPG", ".jpg"), ("avatar", "")])
    def test_generate_new_filename_with_uuid(self, mocker, original, expected_ext):
        mock_uuid = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mocker.patch("users.services.avatars.uuid.uuid4", return_value=mock_uuid)

        filename = generate_new_filename_with_uuid(original)
        assert filename == f"12345678123456781234567812345678{expected_ext}"

    def test_avatar_upload_to(self, mocker, mock_user):
        mock_gen = mocker.patch(
            "users.services.avatars.generate_new_filename_with_uuid", return_value="uuid.png"
        )
        assert avatar_upload_to(mock_user, "photo.png") == "avatars/uuid.png"
        mock_gen.assert_called_once_with("photo.png")

    @pytest.mark.parametrize(
        "pk, expected_prefix",
        [
            (15, "avatars/15/"),
            (None, "avatars/tmp/"),
        ],
    )
    def test_user_avatar_upload_path(self, mocker, pk, expected_prefix):
        mock_gen = mocker.patch(
            "users.services.avatars.generate_new_filename_with_uuid", return_value="uuid.png"
        )
        user = mocker.Mock(pk=pk)

        assert user_avatar_upload_path(user, "photo.png") == f"{expected_prefix}uuid.png"
        mock_gen.assert_called_once_with("photo.png")

    def test_get_storage_path_to_avatar_with_ext(self, mock_user):
        root, ext = get_storage_path_to_avatar_with_ext(mock_user)
        assert root == "avatars/5/avatar"
        assert ext == ".png"


class TestStorageAndDbUtils:
    """
    Тестирование сохранения, получения и удаления файлов.
    """

    def test_save_img_in_storage(self, mocker):
        storage = mocker.patch("users.services.avatars.storage_default")
        buffer = io.BytesIO(b"image-bytes")
        buffer.read(3)

        save_img_in_storage(buffer, "avatars/1/small.png")

        storage.save.assert_called_once()
        path, content = storage.save.call_args.args
        assert path == "avatars/1/small.png"
        assert isinstance(content, ContentFile)
        assert content.read() == b"image-bytes"

    def test_get_user_avatar_paths_list(self, mock_user):
        # В фикстуре задано user.avatar.name = "avatars/5/avatar.png"
        mock_user.avatar_small_size1.name = "avatars/5/small1.png"
        mock_user.avatar_small_size2.name = mock_user.DEFAULT_AVATAR_SMALL_SIZE2_FILENAME
        mock_user.avatar_small_size3.name = ""

        # Список имен полей миниатюр аватара
        mock_user.get_small_avatar_fields.return_value = [
            "avatar_small_size1",
            "avatar_small_size2",
            "avatar_small_size3",
        ]

        paths = get_user_avatar_paths_list(mock_user)
        # Проверка списка путей всех файлов аватаров пользователя, исключая стандартные.
        assert paths == ["avatars/5/avatar.png", "avatars/5/small1.png", ""]

    def test_get_old_avatar_names_no_pk(self, mock_user):
        mock_user.pk = None
        assert get_old_avatar_names(mock_user) == (None, [])

    def test_get_old_avatar_names_unchanged_avatars(self, mocker, mock_user):
        old_user = mocker.Mock()
        old_user.avatar.name = mock_user.avatar.name

        mocker.patch("users.models.User.objects.get", return_value=old_user)

        name, to_delete = get_old_avatar_names(mock_user)
        assert to_delete == []

    def test_get_old_avatar_names_changed_avatars(self, mocker, mock_user):
        old_user = mocker.Mock()
        old_avatars = [
            "avatars/5/avatar_old.png",
            "avatars/5/avatar_old_small1.png",
            "avatars/5/avatar_old_small2.png",
        ]
        old_user.avatar.name = old_avatars[0]

        mocker.patch("users.models.User.objects.get", return_value=old_user)

        mocker.patch("users.services.avatars.get_user_avatar_paths_list", return_value=old_avatars)

        name, to_delete = get_old_avatar_names(mock_user)
        assert name == "avatars/5/avatar_old.png"
        assert to_delete == old_avatars

    def test_delete_old_avatar_names(self, mocker):
        storage = mocker.patch("users.services.avatars.storage_default")
        storage.exists.return_value = True
        storage.delete.side_effect = [None, BotoCoreError()]

        delete_old_avatar_names(
            ["avatars/5/avatar_old_small1.png", "avatars/5/avatar_old_small2.png"]
        )
        assert storage.delete.call_count == 2


class TestAvatarGeneration:
    """
    Тестирование генерации миниатюр аватарки.
    """

    @pytest.mark.parametrize(
        "avatar_name, size_type, expected",
        [
            ("", 1, False),
            (User.DEFAULT_AVATAR_FILENAME, 1, False),
            ("avatar/avatar.png", 99, False),
        ],
    )
    def test_generate_avatar_small_early_exits(self, mock_user, avatar_name, size_type, expected):
        mock_user.avatar.name = avatar_name
        assert generate_avatar_small(mock_user, size_type) is expected

    def test_generate_avatar_small_already_exists(self, mocker, mock_user):
        """Проверяет, что если миниатюра есть, перегенерации не происходит."""
        mocker.patch("users.services.avatars.storage_default.exists", return_value=True)
        mock_save = mocker.patch("users.services.avatars.save_img_in_storage")
        mock_open = mocker.patch("users.services.avatars.Image.open")

        result = generate_avatar_small(mock_user, 1)

        assert result == "avatars/5/avatar_small_size1.png"
        mock_save.assert_not_called()
        mock_open.assert_not_called()

    def test_generate_avatar_small_success(self, mocker, mock_user):
        storage = mocker.patch("users.services.avatars.storage_default")
        storage.exists.return_value = False

        # MagicMock для подмены объекта в блоке with, имеет пустой .__exit__()
        image_mock = mocker.MagicMock()
        mock_image_open = mocker.patch("users.services.avatars.Image.open")
        mock_image_open.return_value.__enter__.return_value = image_mock

        mocker.patch("users.services.avatars.generate_image", return_value=io.BytesIO(b"img"))
        save_mock = mocker.patch("users.services.avatars.save_img_in_storage")

        result = generate_avatar_small(mock_user, 1)

        assert result == "avatars/5/avatar_small_size1.png"
        save_mock.assert_called_once()

    @pytest.mark.parametrize("exception", [OSError, BotoCoreError])
    def test_generate_avatar_small_errors(self, mocker, mock_user, exception):
        mocker.patch("users.services.avatars.storage_default.exists", return_value=False)
        mocker.patch("users.services.avatars.Image.open", side_effect=exception())

        assert generate_avatar_small(mock_user, 1) is False

    def test_generate_default_avatar_in_different_sizes(self, mocker, mock_user):
        storage = mocker.patch("users.services.avatars.storage_default")
        storage.exists.return_value = True

        # MagicMock, чтобы отследить вызовы seek()
        file_mock = mocker.MagicMock()
        storage.open.return_value.__enter__.return_value = file_mock

        gen_mock = mocker.patch("users.services.avatars.generate_default_avatar_small")

        generate_default_avatar_in_different_sizes(User)

        assert gen_mock.call_count == 3
        assert file_mock.seek.call_count == 3

        # Проверка аргументов первого вызова
        gen_mock.assert_any_call(User, file_mock, mock_user.DEFAULT_AVATAR_SMALL_SIZE1_FILENAME, 1)

    def test_generate_default_avatar_small_success(self, mocker, mock_user):
        image_mock = mocker.MagicMock()
        mock_image_open = mocker.patch("users.services.avatars.Image.open")
        mock_image_open.return_value.__enter__.return_value = image_mock

        mocker.patch("users.services.avatars.generate_image", return_value=io.BytesIO(b"img"))
        save_mock = mocker.patch("users.services.avatars.save_img_in_storage")

        generate_default_avatar_small(
            User, io.BytesIO(b"file"), mock_user.DEFAULT_AVATAR_SMALL_SIZE1_FILENAME, 1
        )

        save_mock.assert_called_once()

    def test_generate_default_avatar_small_error(self, mocker, mock_user):
        mocker.patch("users.services.avatars.Image.open", side_effect=BotoCoreError())
        save_mock = mocker.patch("users.services.avatars.save_img_in_storage")

        generate_default_avatar_small(
            mock_user.__class__,
            io.BytesIO(b"file"),
            mock_user.DEFAULT_AVATAR_SMALL_SIZE1_FILENAME,
            1,
        )
        save_mock.assert_not_called()
