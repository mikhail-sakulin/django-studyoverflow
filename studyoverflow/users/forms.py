from typing import Protocol, runtime_checkable

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm,
    UserCreationForm,
)
from django.core.exceptions import ValidationError
from django.forms import ClearableFileInput
from django.utils import timezone
from django.utils.translation import gettext_lazy


@runtime_checkable
class FormProtocol(Protocol):
    """
    Протокол, определяющий обязательные атрибуты формы для работы BootstrapFormMixin.
    """

    fields: dict
    is_bound: bool
    errors: dict


class BootstrapFormMixin:
    """
    Миксин для добавления Bootstrap-оформления полям формы.

    Добавляет:
        - класс form-control ко всем полям;
        - placeholder = label (если не задан);
        - классы is-valid / is-invalid для полей при POST-запросе.
    """

    def _apply_bootstrap_styles(self, *args, **kwargs):
        if not isinstance(self, FormProtocol):
            raise TypeError("BootstrapFormMixin требует наличия fields, is_bound, errors")

        for field_name, field in self.fields.items():
            css_classes = field.widget.attrs.get("class", "")

            # Добавление css-класса "form-control"
            field.widget.attrs["class"] = f"{css_classes} form-control".strip()

            # Добавление placeholder
            if "placeholder" not in field.widget.attrs:
                field.widget.attrs["placeholder"] = field.label

            # Добавление классов валидности полей is-valid / is-invalid для
            # уже заполненной формы (POST данными)
            if self.is_bound:
                if field_name in self.errors:
                    field.widget.attrs["class"] += " is-invalid"
                else:
                    field.widget.attrs["class"] += " is-valid"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap_styles(*args, **kwargs)


class UserRegisterForm(BootstrapFormMixin, UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ["username", "first_name", "last_name", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Добавление "is-invalid" к password1, если password2 "is-invalid"
        if "password2" in self.errors and "password1" not in self.errors:
            self.fields["password1"].widget.attrs["class"] += " is-invalid"

    def clean_username(self):
        """
        Валидация поля username.
        """
        username = super().clean_username()

        if username and len(username) < 4:
            raise forms.ValidationError("Длина имени пользователя должна быть не менее 4 символов.")

        return username


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Имя пользователя или email",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Имя пользователя или email"}
        ),
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Пароль"}),
    )
    error_messages = {
        "invalid_login": gettext_lazy("Неверное имя пользователя (или email) или неверный пароль."),
        "inactive": gettext_lazy("This account is inactive."),
    }

    class Meta:
        model = get_user_model()
        fields = ["username", "password"]

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)

        if user.is_blocked:
            if user.blocked_at:
                local_date_block = timezone.localtime(user.blocked_at)
                date_str = local_date_block.strftime("%d.%m.%Y г. %H:%M")
            else:
                date_str = '"неизвестно"'

            raise ValidationError(f"Ваш аккаунт заблокирован в {date_str}.", code="blocked")


class CustomClearableFileInput(ClearableFileInput):
    """
    Кастомный виджет для поля ImageField (аватар пользователя),
    наследуется от стандартного ClearableFileInput.
    """

    clear_checkbox_label = gettext_lazy("Удалить")
    initial_text = gettext_lazy("(используется)")
    input_text = gettext_lazy("Изменить аватар")


class UserProfileUpdateForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ["avatar", "username", "email", "date_birth", "bio", "first_name", "last_name"]
        widgets = {
            "avatar": CustomClearableFileInput(),
            "bio": forms.Textarea(
                attrs={
                    "class": "bio-textarea",
                    "style": "height:150px; overflow-y:auto; resize:vertical;",
                }
            ),
            "date_birth": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }


class UserPasswordChangeForm(BootstrapFormMixin, PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Добавление "is-invalid" к new_password1, если new_password2 "is-invalid"
        if "new_password2" in self.errors and "new_password1" not in self.errors:
            self.fields["new_password1"].widget.attrs["class"] += " is-invalid"


class UserPasswordResetForm(BootstrapFormMixin, PasswordResetForm):
    pass


class UserSetPasswordForm(BootstrapFormMixin, SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Добавление "is-invalid" к new_password1, если new_password2 "is-invalid"
        if "new_password2" in self.errors and "new_password1" not in self.errors:
            self.fields["new_password1"].widget.attrs["class"] += " is-invalid"
