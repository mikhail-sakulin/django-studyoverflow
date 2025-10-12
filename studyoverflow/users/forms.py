from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm


class UserRegisterForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ["username", "first_name", "last_name", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        """
        Переопределение __init__:
            - Добавляет Bootstrap-класс form-control ко всем полям формы.
            - Задает placeholder всем полям формы, если ещё не задан.
            - Добавляет классы валидности полей is-valid / is-invalid.
        """
        super().__init__(*args, **kwargs)
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
