import io
import os
import uuid
from types import SimpleNamespace

import pytest
from botocore.exceptions import BotoCoreError
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from PIL import Image

from users.services.avatars import (
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
    storage_default,
    user_avatar_upload_path,
)


User = get_user_model()


def make_png_bytes(size: tuple[int, int] = (400, 400)) -> bytes:
    """Создает байты (содержимое) PNG-картинки в ОП заданного размера."""
    buffer = io.BytesIO()
    Image.new("RGB", size, "red").save(buffer, format="PNG")
    return buffer.getvalue()


def put_image(path: str, size: tuple[int, int] = (400, 400)) -> str:
    """
    Создает PNG-картинку, кладет ее в storage_default (InMemoryStorage для тестов) и
    возвращает имя файла внутри хранилища.
    """
    return storage_default.save(path, ContentFile(make_png_bytes(size)))


def unique_path(filename: str) -> str:
    """Возвращает уникальный путь внутри хранилища."""
    return f"avatars/{uuid.uuid4()}/{filename}"


def delete_default_avatar_files() -> None:
    """Удаляет из хранилища стандартный аватар и его миниатюры, если они там есть."""
    for name in (
        User.DEFAULT_AVATAR_FILENAME,
        User.DEFAULT_AVATAR_SMALL_SIZE1_FILENAME,
        User.DEFAULT_AVATAR_SMALL_SIZE2_FILENAME,
        User.DEFAULT_AVATAR_SMALL_SIZE3_FILENAME,
    ):
        if storage_default.exists(name):
            storage_default.delete(name)


def image_size_in_storage(name: str) -> tuple[int, int]:
    """Возвращает размер картинки, лежащей в хранилище."""
    # Также допустимо записать:
    #   with storage_default.open(name) as file, Image.open(file) as img: ...
    with storage_default.open(name) as file:
        with Image.open(file) as img:
            return img.size


class TestFilenamesAndPaths:
    """
    Тестирование путей и имен файлов.
    """

    @pytest.mark.parametrize("original, expected_ext", [("photo.JPG", ".jpg"), ("avatar", "")])
    def test_generate_new_filename_with_uuid(self, mocker, original, expected_ext):
        """
        Имя файла заменяется на uuid, расширение сохраняется в нижнем регистре,
        для файла без расширения оно остается пустым.
        """
        uuid_hex = "12345678123456781234567812345678"
        mock_uuid = uuid.UUID(uuid_hex)
        mocker.patch("users.services.avatars.uuid.uuid4", return_value=mock_uuid)

        filename = generate_new_filename_with_uuid(original)
        assert filename == f"{uuid_hex}{expected_ext}"

    def test_avatar_upload_to(self, mocker):
        """
        Старый путь загрузки аватара, не используемый в текущей версии проекта,
        имеет вид avatars/<uuid>.<ext>.
        """
        uuid_hex = "12345678123456781234567812345678"
        mock_uuid = uuid.UUID(uuid_hex)
        mocker.patch("users.services.avatars.uuid.uuid4", return_value=mock_uuid)

        # instance (user) в функции не используется
        assert avatar_upload_to(SimpleNamespace(), "photo.png") == (  # type: ignore
            f"avatars/{uuid_hex}.png"
        )

    def test_user_avatar_upload_path(self, mocker):
        """Путь загрузки аватара имеет вид avatars/<s3_storage_uuid>/<uuid>.<ext>."""
        uuid_hex = "12345678123456781234567812345678"
        mock_uuid = uuid.UUID(uuid_hex)
        mocker.patch("users.services.avatars.uuid.uuid4", return_value=mock_uuid)

        user = SimpleNamespace(s3_storage_uuid="123e4567-e89b-12d3-a456-426614174000")

        expected_path = f"avatars/{user.s3_storage_uuid}/{uuid_hex}.png"
        assert user_avatar_upload_path(user, "photo.png") == expected_path  # type: ignore

    def test_get_storage_path_to_avatar_with_ext(self):
        """
        Проверяет функцию get_storage_path_to_avatar_with_ext, которая возвращает
        кортеж (путь без расширения, расширение файла) для avatar пользователя.
        """
        user = SimpleNamespace(avatar=SimpleNamespace(name="avatars/5/avatar.png"))

        root, ext = get_storage_path_to_avatar_with_ext(user)  # type: ignore
        assert root == "avatars/5/avatar"
        assert ext == ".png"


@pytest.mark.django_db
class TestStorageAndDbUtils:
    """
    Тестирование сохранения, получения и удаления файлов.
    """

    def test_save_img_in_storage(self):
        """Содержимое буфера (картинка) сохраняется в хранилище целиком."""
        path_in_storage = unique_path("small.png")
        buffer = io.BytesIO(b"image-bytes")
        # Тестируемая функция должна сама возвращаться в начало буфера
        buffer.read(3)

        save_img_in_storage(buffer, path_in_storage)

        with storage_default.open(path_in_storage) as file:
            assert file.read() == b"image-bytes"

    def test_get_user_avatar_paths_list(self, user_factory):
        """В список попадают пути аватара и миниатюр, стандартные и пустые значения исключаются."""
        # Миниатюра size2 стандартная, size3 пустая
        user = user_factory(
            avatar="avatars/5/avatar.png",
            avatar_small_size1="avatars/5/avatar_small1.png",
            avatar_small_size3="",
        )

        # Возвращаются пути файлов аватаров, исключаются стандартные и пустые.
        paths = get_user_avatar_paths_list(user)
        assert paths == ["avatars/5/avatar.png", "avatars/5/avatar_small1.png"]

    def test_get_old_avatar_names_no_pk(self):
        """Для пользователя без pk (не сохраненного в БД) возвращается (None, [])."""
        assert get_old_avatar_names(User()) == (None, [])

    def test_get_old_avatar_names_unchanged_avatars(self, user_factory):
        """Если аватар не менялся, список файлов на удаление пуст."""
        user = user_factory(avatar="avatars/5/avatar.png")

        name, to_delete = get_old_avatar_names(user)

        assert name == "avatars/5/avatar.png"
        assert to_delete == []

    def test_get_old_avatar_names_changed_avatars(self, user_factory):
        """
        Если аватар изменен, возвращается имя аватара из БД и список старых файлов
        (аватар и миниатюры), которые нужно удалить.
        """
        old_avatars = [
            "avatars/5/avatar_old.png",
            "avatars/5/avatar_old_small1.png",
            "avatars/5/avatar_old_small2.png",
        ]
        user = user_factory(
            avatar=old_avatars[0],
            avatar_small_size1=old_avatars[1],
            avatar_small_size2=old_avatars[2],
        )
        # В БД лежат старые значения, у python-объекта задается новый аватар
        user.avatar = "avatars/5/avatar_new.png"

        name, to_delete = get_old_avatar_names(user)

        assert name == "avatars/5/avatar_old.png"
        assert to_delete == old_avatars

    def test_delete_old_avatar_names(self):
        """Файлы из списка удаляются из хранилища, пустые имена пропускаются."""
        first = put_image(unique_path("small1.png"))
        second = put_image(unique_path("small2.png"))

        # Пустые имена пропускаются
        delete_old_avatar_names([first, "", second])

        assert not storage_default.exists(first)
        assert not storage_default.exists(second)

    def test_delete_old_avatar_names_storage_error_does_not_stop_the_rest(self, mocker):
        """Ошибка хранилища при удалении одного файла не мешает удалить остальные."""
        first = put_image(unique_path("small1.png"))
        second = put_image(unique_path("small2.png"))
        real_delete_not_mock = storage_default.delete

        def flaky_delete(name):
            if name == first:
                raise BotoCoreError()
            real_delete_not_mock(name)

        mocker.patch.object(storage_default, "delete", side_effect=flaky_delete)

        delete_old_avatar_names([first, second])

        assert storage_default.exists(first)
        assert not storage_default.exists(second)


@pytest.mark.django_db
class TestAvatarGeneration:
    """
    Тестирование генерации миниатюр аватарки.
    """

    @pytest.fixture
    def default_avatar_in_storage(self):
        """
        Помещает в хранилище стандартный аватар (большой, чтобы миниатюры
        получили полные размеры) и убирает все файлы по окончании теста.
        """
        delete_default_avatar_files()
        put_image(User.DEFAULT_AVATAR_FILENAME, size=(1000, 1000))
        yield
        delete_default_avatar_files()

    @pytest.mark.parametrize(
        "avatar_name, size_type, expected",
        [
            ("", 1, False),
            (User.DEFAULT_AVATAR_FILENAME, 1, False),
            ("avatar/avatar.png", 99, False),
        ],
    )
    def test_generate_avatar_small_early_exits(
        self, user_factory, avatar_name, size_type, expected
    ):
        """
        Миниатюра не создается и возвращается False, если аватара нет, он стандартный
        или передан неверный номер размера миниатюры.
        """
        user = user_factory(avatar=avatar_name)

        assert generate_avatar_small(user, size_type) is expected

    def test_generate_avatar_small_already_exists(self, user_factory):
        """Проверяет, что если миниатюра же существует, то перегенерации не происходит."""
        avatar_name = put_image(unique_path("avatar.png"))
        root, ext = os.path.splitext(avatar_name)
        # Миниатюра уже существует, задано другое содержимое (отличное от оригинала) для
        # проверки отсутствия перегенерации.
        existing_small = storage_default.save(f"{root}_small_size1{ext}", ContentFile(b"old"))
        user = user_factory(avatar=avatar_name)

        result = generate_avatar_small(user, size_type=1)

        assert result == existing_small
        with storage_default.open(existing_small) as file:
            assert file.read() == b"old"

    def test_generate_avatar_small_success(self, user_factory):
        """Миниатюра создается в хранилище с нужным размером, возвращается ее путь."""
        avatar_name = put_image(unique_path("avatar.png"), size=(400, 400))
        user = user_factory(avatar=avatar_name)

        result = generate_avatar_small(user, size_type=1)

        root, ext = os.path.splitext(avatar_name)
        assert isinstance(result, str)
        assert result == f"{root}_small_size1{ext}"
        # Миниатюра создана и имеет нужный размер (size1 = 100x100)
        assert image_size_in_storage(result) == (100, 100)

    @pytest.mark.parametrize("exception", [ValueError, BotoCoreError])
    def test_generate_avatar_small_storage_errors(self, mocker, user_factory, exception):
        """Исключения при сохранении миниатюры не пробрасываются, возвращается False."""
        avatar_name = put_image(unique_path("avatar.png"))
        user = user_factory(avatar=avatar_name)
        mocker.patch.object(storage_default, "save", side_effect=exception)

        assert generate_avatar_small(user, 1) is False

    def test_generate_default_avatar_in_different_sizes(self, default_avatar_in_storage):
        """Из стандартного аватара создаются миниатюры всех размеров."""
        generate_default_avatar_in_different_sizes(User)

        assert image_size_in_storage(User.DEFAULT_AVATAR_SMALL_SIZE1_FILENAME) == (100, 100)
        assert image_size_in_storage(User.DEFAULT_AVATAR_SMALL_SIZE2_FILENAME) == (170, 170)
        assert image_size_in_storage(User.DEFAULT_AVATAR_SMALL_SIZE3_FILENAME) == (800, 800)

    def test_generate_default_avatar_small_success(self):
        """Миниатюра стандартного аватара сохраняется в хранилище с нужным размером."""
        path = unique_path("default_avatar_small_size1.jpg")

        generate_default_avatar_small(User, io.BytesIO(make_png_bytes()), path, size_type=1)

        assert image_size_in_storage(path) == (100, 100)

    def test_generate_default_avatar_small_error(self):
        """Если файл не является картинкой, исключение не пробрасывается, миниатюра не создается."""
        path = unique_path("default_avatar_small_size1.jpg")

        # Файл не является картинкой, исключение не пробрасывается, миниатюра не создается
        generate_default_avatar_small(User, io.BytesIO(b"not an image"), path, size_type=1)

        assert not storage_default.exists(path)

    def test_generate_default_avatar_small_storage_error(self, mocker):
        """Ошибка хранилища (S3) при сохранении миниатюры не пробрасывается."""
        path = unique_path("default_avatar_small_size1.jpg")
        mocker.patch.object(storage_default, "save", side_effect=BotoCoreError())

        generate_default_avatar_small(User, io.BytesIO(make_png_bytes()), path, size_type=1)

        assert not storage_default.exists(path)
