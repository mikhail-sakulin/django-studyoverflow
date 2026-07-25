import io
from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from PIL import Image

from users.services import (
    AvatarFileValidator,
    BirthDateValidator,
    CustomUsernameValidator,
    PersonalNameValidator,
    validate_email_unique,
)


class TestCustomUsernameValidator:

    @pytest.fixture
    def validator(self):
        return CustomUsernameValidator()

    @pytest.mark.parametrize(
        "valid_username",
        [
            "john",
            "alex_99",
            "super-user",
            "USER-name_",
        ],
    )
    def test_valid_usernames(self, validator, valid_username):
        assert validator(valid_username) is None

    @pytest.mark.parametrize(
        "invalid_username",
        [
            "",
            "abc",
            "new alex",
            "user!",
            "юзер",
        ],
    )
    def test_invalid_username(self, validator, invalid_username):
        with pytest.raises(ValidationError) as exc:
            validator(invalid_username)

        assert exc.value.code == "invalid_username"


class TestPersonalNameValidator:

    @pytest.fixture
    def validator(self):
        return PersonalNameValidator()

    @pytest.mark.parametrize(
        "valid_name",
        [
            "",
            "John",
            "Anna-Maria",
        ],
    )
    def test_valid_names(self, validator, valid_name):
        assert validator(valid_name) is None

    @pytest.mark.parametrize(
        ("invalid_name", "code"),
        [
            ("Jake Smith", "name_contains_spaces"),
            ("name!", "invalid_name_characters"),
            ("name123", "invalid_name_characters"),
            ("-", "name_only_hyphens"),
            ("-Jake", "name_edge_hyphen"),
            ("Jake-", "name_edge_hyphen"),
            ("Anna--Maria", "name_double_hyphen"),
        ],
    )
    def test_invalid_names(self, validator, invalid_name, code):
        with pytest.raises(ValidationError) as exc:
            validator(invalid_name)

        assert exc.value.code == code


def create_uploaded_image(width: int, height: int, fmt: str = "PNG") -> SimpleUploadedFile:
    """
    Создает тестовое изображение в оперативной памяти.
    """
    buffer = io.BytesIO()

    image = Image.new("RGB", (width, height), color="white")
    image.save(buffer, format=fmt)

    buffer.seek(0)

    # SimpleUploadedFile - имитация загруженного клиентом файла для тестирования,
    # наследуется от InMemoryUploadedFile, а он от UploadedFile,
    # (в валидаторе AvatarFileValidator проверяется тип UploadedFile).
    return SimpleUploadedFile(
        name=f"avatar.{fmt.lower()}",
        content=buffer.read(),
        content_type=f"image/{fmt.lower()}",
    )


class TestAvatarFileValidator:

    @pytest.fixture
    def validator(self):
        return AvatarFileValidator()

    def test_skip_validation_for_not_uploaded_file(self, validator):
        """Если аватарка не обновлялась, то валидация пропускается."""
        file = File(io.BytesIO(b"old file"))

        assert validator(file) is None

    @pytest.mark.parametrize(
        ("width", "height", "fmt"),
        [
            (100, 100, "PNG"),
            (200, 200, "JPEG"),
            (400, 100, "WEBP"),
            (100, 400, "GIF"),
        ],
    )
    def test_valid_avatar(self, validator, width, height, fmt):
        avatar = create_uploaded_image(width, height, fmt)

        assert validator(avatar) is None

    def test_file_too_large(self, validator):
        avatar = create_uploaded_image(100, 100)

        avatar.size = validator.MAX_SIZE + 1

        with pytest.raises(ValidationError) as exc:
            validator(avatar)

        assert exc.value.code == "file_too_large"

    def test_filetype_read_file_error(self, validator, mocker):
        avatar = create_uploaded_image(100, 100)

        # mocker - фикстура из pytest-mock
        mocker.patch(
            "users.services.validators.filetype.guess",
            side_effect=RuntimeError,
        )

        with pytest.raises(ValidationError) as exc:
            validator(avatar)

        assert exc.value.code == "could_not_read"

    def test_invalid_file_type(self, validator):
        bad_file = SimpleUploadedFile(
            "file.txt",
            b"text",
            content_type="text/plain",
        )

        with pytest.raises(ValidationError) as exc:
            validator(bad_file)

        assert exc.value.code == "invalid_file_type"

    @pytest.mark.parametrize(
        ("width", "height"),
        [
            (99, 100),
            (100, 99),
            (50, 50),
        ],
    )
    def test_image_too_small(self, validator, width, height):
        avatar = create_uploaded_image(width, height)

        with pytest.raises(ValidationError) as exc:
            validator(avatar)

        assert exc.value.code == "file_too_small"

    @pytest.mark.parametrize(
        ("width", "height"),
        [
            (401, 100),
            (100, 401),
        ],
    )
    def test_invalid_aspect_ratio(self, validator, width, height):
        avatar = create_uploaded_image(width, height)

        with pytest.raises(ValidationError) as exc:
            validator(avatar)

        assert exc.value.code == "invalid_file_aspect_ration"


class TestBirthDateValidator:

    @pytest.fixture
    def validator(self):
        return BirthDateValidator()

    def test_valid_birth_date(self, validator):
        birth_date = timezone.localdate() - timedelta(days=365 * 30)

        assert validator(birth_date) is None

    def test_future_birth_date(self, validator):
        birth_date = timezone.localdate() + timedelta(days=1)

        with pytest.raises(ValidationError) as exc:
            validator(birth_date)

        assert exc.value.code == "future_date"

    def test_age_exceeds_maximum(self, validator):
        today = timezone.localdate()

        birth_date = today.replace(year=today.year - validator.MAX_AGE - 1)

        with pytest.raises(ValidationError) as exc:
            validator(birth_date)

        assert exc.value.code == "max_age_exceeded"

    def test_maximum_allowed_age(self, validator):
        today = timezone.localdate()

        birth_date = today.replace(year=today.year - validator.MAX_AGE)

        assert validator(birth_date) is None


@pytest.mark.django_db
class TestValidateEmailUnique:

    def test_unique_email(self) -> None:
        validate_email_unique("john@example.com")

    def test_duplicate_email_same_case(self, user_factory):
        user_factory(email="john@example.com")

        with pytest.raises(ValidationError) as exc:
            validate_email_unique("john@example.com")

        assert exc.value.code == "email_exists"

    def test_duplicate_email_different_case(self, user_factory):
        user_factory(email="John@Example.com")

        with pytest.raises(ValidationError) as exc:
            validate_email_unique("john@example.com")

        assert exc.value.code == "email_exists"

    def test_ignore_current_instance(self, user_factory):
        user = user_factory(email="john@example.com")

        validate_email_unique("JOHN@example.com", instance=user)

    def test_email_exists_for_another_user(self, user_factory):
        current_user = user_factory(email="john@example.com")
        user_factory(email="alex@example.com")

        with pytest.raises(ValidationError) as exc:
            validate_email_unique(
                "Alex@Example.com",
                instance=current_user,
            )

        assert exc.value.code == "email_exists"
