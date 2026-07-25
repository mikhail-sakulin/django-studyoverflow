from types import SimpleNamespace

import pytest
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from users.forms import (
    BootstrapFormMixin,
    UserLoginForm,
    UserProfileUpdateForm,
    UserRegisterForm,
    UserSetPasswordForm,
)


class SampleForm(BootstrapFormMixin, forms.Form):
    name = forms.CharField(label="Имя пользователя")
    email = forms.EmailField(label="Электронная почта")


class TestBootstrapFormMixin:
    def test_apply_bootstrap_classes_and_placeholders_by_default(self):
        """Добавляет CSS-классы Bootstrap и плейсхолдеры к полям формы при инициализации."""
        form = SampleForm()

        assert "form-control" in form.fields["name"].widget.attrs["class"]
        assert "form-control" in form.fields["email"].widget.attrs["class"]
        assert form.fields["name"].widget.attrs["placeholder"] == "Имя пользователя"
        assert form.fields["email"].widget.attrs["placeholder"] == "Электронная почта"

    def test_validation_classes_applied_when_form_is_bound(self):
        """
        Добавляет классы is-valid / is-invalid к полям в зависимости от успешности их валидации.
        """
        form = SampleForm(data={"name": "Alex", "email": "не_email"})
        form.is_valid()

        assert "is-valid" in form.fields["name"].widget.attrs["class"]
        assert "is-invalid" in form.fields["email"].widget.attrs["class"]


@pytest.mark.django_db
class TestUserRegisterForm:
    def test_username_length_validation(self):
        """Имя пользователя должно быть длиной не менее 4 символов."""
        form = UserRegisterForm(data={"username": "abc"})
        assert not form.is_valid()
        assert "username" in form.errors
        assert (
            "Длина имени пользователя должна быть не менее 4 символов." in form.errors["username"]
        )

    def test_password_styling_propagation_on_error(self):
        """Если второй пароль не совпал с первым, is-invalid класс у обоих полей паролей."""
        form = UserRegisterForm(
            data={
                "password1": "Password123!",
                "password2": "DifferentPassword123!",
            }
        )
        form.is_valid()

        assert "is-invalid" in form.fields["password1"].widget.attrs["class"]
        assert "is-invalid" in form.fields["password1"].widget.attrs["class"]

    def test_email_uniqueness_validation(self, user_factory):
        """Форма проверяет уникальность email."""
        user_factory(email="existing@example.com")

        form = UserRegisterForm(data={"email": "EXISTING@example.com"})
        form.is_valid()

        assert "email" in form.errors


class TestUserLoginForm:
    def test_login_denied_for_blocked_users(self):
        """Заблокированный пользователь не может залогиниться."""
        block_time = timezone.now()
        blocked_user = SimpleNamespace(is_active=True, is_blocked=True, blocked_at=block_time)
        form = UserLoginForm()

        with pytest.raises(ValidationError) as exc_info:
            form.confirm_login_allowed(blocked_user)

        date_str = timezone.localtime(block_time).strftime("%d.%m.%Y г. %H:%M")
        assert f"Ваш аккаунт заблокирован {date_str}." in exc_info.value.message


@pytest.mark.django_db
class TestUserProfileUpdateForm:
    def test_email_uniqueness_excluding_current_user(self, user_factory):
        """Пользователь может оставить свой email, но не может дублировать чужой."""
        user1 = user_factory(email="first@example.com")
        user_factory(email="second@example.com")

        form_self = UserProfileUpdateForm(
            instance=user1, data={"username": "user1", "email": "first@example.com"}
        )
        assert "email" not in form_self.errors

        form_email_duplication = UserProfileUpdateForm(
            instance=user1, data={"username": "user1", "email": "second@example.com"}
        )
        form_email_duplication.is_valid()
        assert "email" in form_email_duplication.errors


class TestUserSetPasswordForm:
    def test_set_password_denied_for_social_accounts(self):
        """Пользователи, вошедшие через социальные сети, не могут установить пароль."""
        social_user = SimpleNamespace(is_social=True)
        form = UserSetPasswordForm(user=social_user, data={})

        assert not form.is_valid()

        expected_error = "Пользователи, зарегистрированные через социальные сети"
        assert any(expected_error in error for error in form.non_field_errors())
