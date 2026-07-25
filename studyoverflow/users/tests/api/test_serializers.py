from types import SimpleNamespace

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.exceptions import ValidationError
from users.api.serializers import (
    PasswordResetConfirmSerializer,
    UserMyProfileSerializer,
    UserPasswordChangeSerializer,
    UserRegisterSerializer,
)


User = get_user_model()


@pytest.mark.django_db
class TestUserMyProfileSerializer:
    """Тестирование профиля авторизованного пользователя."""

    def test_validate_username_exists(self, user_factory):
        """Проверка уникальности username без учета регистра, если username занят."""
        user_factory(username="Root_User")
        serializer = UserMyProfileSerializer()

        with pytest.raises(ValidationError) as exc:
            serializer.validate_username("root_user")

        assert "уже существует" in str(exc.value.detail[0])

    def test_validate_username_self_update(self, user_factory):
        """При обновлении профиля пользователь может поменять регистр своего username."""
        user = user_factory(username="Root_User")
        # Передается instance, чтобы сериализатор знал, кого обновлять
        serializer = UserMyProfileSerializer(instance=user)

        result = serializer.validate_username("root_user")
        assert result == "root_user"

    def test_validate_username_success(self):
        """Новый уникальный username проходит валидацию."""
        serializer = UserMyProfileSerializer()
        result = serializer.validate_username("new_unique_user")
        assert result == "new_unique_user"


@pytest.mark.django_db
class TestUserRegisterSerializer:
    """Тестирование регистрации пользователя."""

    def test_passwords_mismatch(self):
        """Пароли при регистрации должны совпадать."""
        serializer = UserRegisterSerializer()
        attrs = {"password": "Password123!", "password_confirm": "Password321!"}

        with pytest.raises(ValidationError) as exc:
            serializer.validate(attrs)

        assert "password_confirm" in exc.value.detail

    def test_password_validation_called(self, mocker):
        """Проверка, что пароль прогоняется через встроенные валидаторы Django."""
        serializer = UserRegisterSerializer()
        attrs = {"username": "new_user", "password": "weak", "password_confirm": "weak"}

        mock_validate = mocker.patch(
            "users.api.serializers.validate_password",
            side_effect=DjangoValidationError("Слишком простой пароль."),
        )

        with pytest.raises(ValidationError) as exc:
            serializer.validate(attrs)

        assert "password" in exc.value.detail
        mock_validate.assert_called_once()

    def test_validate_username_exists(self, user_factory):
        """Проверка уникальности username без учета регистра, если username занят."""
        user_factory(username="Root_User")
        serializer = UserRegisterSerializer()

        with pytest.raises(ValidationError) as exc:
            serializer.validate_username("root_user")

        assert "уже существует" in str(exc.value.detail[0])

    def test_validate_success(self, mocker):
        """Правильные данные проходят валидацию."""
        mocker.patch("users.api.serializers.validate_password")
        serializer = UserRegisterSerializer()
        attrs = {
            "username": "new_user",
            "email": "new@example.com",
            "password": "StrongPassword123",
            "password_confirm": "StrongPassword123",
        }
        result = serializer.validate(attrs)
        assert result == attrs


@pytest.mark.django_db
class TestUserPasswordChangeSerializer:
    """Тестирование смены пароля."""

    def test_invalid_old_password(self, user_factory):
        """Если текущий пароль указан неверно, вызывается ошибка."""
        user = user_factory(password="OldPassword123")

        mock_request = SimpleNamespace(user=user)
        serializer = UserPasswordChangeSerializer(context={"request": mock_request})

        with pytest.raises(ValidationError) as exc:
            serializer.validate_password_old("WrongPassword123")

        assert "Текущий пароль введен неверно" in str(exc.value.detail[0])

    def test_passwords_mismatch(self):
        """Новые пароли должны совпадать."""
        serializer = UserPasswordChangeSerializer()
        attrs = {"password_new": "Password123!", "password_new_confirm": "Password321!"}

        with pytest.raises(ValidationError) as exc:
            serializer.validate(attrs)

        assert "password_new_confirm" in exc.value.detail

    def test_password_validation_called(self, mocker):
        """Проверка, что новый пароль прогоняется через встроенные валидаторы Django."""
        user = SimpleNamespace(username="new_user", password="OldPassword123")
        mock_request = SimpleNamespace(user=user)
        serializer = UserPasswordChangeSerializer(context={"request": mock_request})

        attrs = {"username": "new_user", "password_new": "weak", "password_new_confirm": "weak"}

        mock_validate = mocker.patch(
            "users.api.serializers.validate_password",
            side_effect=DjangoValidationError("Слишком простой пароль."),
        )

        with pytest.raises(ValidationError) as exc:
            serializer.validate(attrs)

        assert "password_new" in exc.value.detail
        mock_validate.assert_called_once()

    def test_validate_success(self, user_factory, mocker):
        """Корректные старый и новые пароли проходят валидацию."""
        user = SimpleNamespace(username="new_user", password="OldPassword123")
        mock_request = SimpleNamespace(user=user)
        serializer = UserPasswordChangeSerializer(context={"request": mock_request})

        mocker.patch("users.api.serializers.validate_password")
        attrs = {
            "password_old": "OldPassword123",
            "password_new": "NewStrongPassword1",
            "password_new_confirm": "NewStrongPassword1",
        }
        result = serializer.validate(attrs)
        assert result == attrs


@pytest.mark.django_db
class TestPasswordResetConfirmSerializer:
    """Тестирование восстановления пароля."""

    def test_invalid_uidb64(self):
        """Передача неверного закодированного ID пользователя вызывает ошибку."""
        serializer = PasswordResetConfirmSerializer()
        attrs = {
            "uidb64": "not_a_base64_string",
            "token": "any_token",
            "password_new": "StrongPassword123",
            "password_new_confirm": "StrongPassword123",
        }

        with pytest.raises(ValidationError) as exc:
            serializer.validate(attrs)

        assert "uidb64" in exc.value.detail

    def test_social_user_cannot_reset_password(self, user_factory, mocker):
        """
        Пользователи, зарегистрированные через соцсети (is_social==True), не могут менять пароль.
        """
        user = user_factory(is_social=True)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

        serializer = PasswordResetConfirmSerializer()
        attrs = {
            "uidb64": uidb64,
            "token": "valid_looking_token",
            "password_new": "Password123_new",
            "password_new_confirm": "Password123_new",
        }

        mocker.patch("users.api.serializers.default_token_generator.check_token", return_value=True)

        with pytest.raises(ValidationError) as exc:
            serializer.validate(attrs)

        assert "через социальные сети" in str(exc.value.detail["detail"])

    def test_validate_success(self, user_factory, mocker):
        """Корректные данные позволяют сбросить пароль."""
        user = user_factory(is_social=False)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

        mocker.patch("users.api.serializers.default_token_generator.check_token", return_value=True)
        mocker.patch("users.api.serializers.validate_password")

        serializer = PasswordResetConfirmSerializer()
        attrs = {
            "uidb64": uidb64,
            "token": "valid_token",
            "password_new": "NewPassword123",
            "password_new_confirm": "NewPassword123",
        }
        result = serializer.validate(attrs)
        assert result == attrs
