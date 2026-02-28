from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from posts.models import Comment, Post
from posts.services import validate_and_normalize_tags, validate_comment
from taggit.forms import TagWidget
from users.services import CustomUsernameValidator


class PostCreateForm(forms.ModelForm):
    """
    Форма создания поста с валидацией длины заголовка, тегов и нормализацией тегов.
    """

    class Meta:
        model = Post
        fields = ["title", "content", "tags"]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Введите заголовок"}
            ),
            "content": forms.Textarea(
                attrs={"class": "form-control", "placeholder": "Введите содержимое...", "rows": 8}
            ),
            "tags": TagWidget(attrs={"class": "form-control", "placeholder": "Введите теги..."}),
        }

    def clean_tags(self):
        """
        Валидация и нормализация тегов.
        """
        tags_list = self.cleaned_data["tags"]

        normalized_tags = validate_and_normalize_tags(tags_list)

        return normalized_tags


class PostFilterForm(forms.Form):
    """
    Форма фильтрации постов по автору с валидацией существования пользователя.
    """

    author = forms.CharField(required=False)

    def clean_author(self):
        author = self.cleaned_data["author"].strip()

        if not author:
            return author

        validator = CustomUsernameValidator()
        try:
            validator(author)
        except ValidationError as e:
            raise ValidationError(e.messages)

        if not get_user_model().objects.filter(username__iexact=author).exists():
            raise ValidationError("Указанного автора не существует.")

        return author


class CommentCreateForm(forms.ModelForm):
    """
    Форма добавления комментария.
    """

    class Meta:
        model = Comment
        fields = ["content", "parent_comment", "reply_to"]
        labels = {"content": "Комментарий (поддерживается синтаксис Markdown)"}
        widgets = {
            "content": forms.Textarea(
                attrs={"class": "form-control", "placeholder": "Комментарий...", "rows": 5}
            ),
        }

    def __init__(self, *args, **kwargs):
        """
        Извлечение пользователя и поста из аргументов для валидации.
        """
        self.user = kwargs.pop("user", None)
        self.post = kwargs.pop("post", None)
        super().__init__(*args, **kwargs)

    def clean(self):
        """
        Валидация иерархии и принадлежности комментария к посту.

        Проверки адаптированы из модели для работы в контексте формы:
        - Поля parent_comment и reply_to должны идти в связке.
        - Все объекты (родитель, ответ) должны принадлежать текущему self.post.
        - Нельзя отвечать самому себе (актуально при редактировании).
        - reply_to должен находиться внутри ветки parent_comment.
        """
        cleaned_data = super().clean()

        # Валидация данных комментария и получение словаря ошибок
        errors = validate_comment(
            content=cleaned_data.get("content"),
            parent_comment=cleaned_data.get("parent_comment"),
            reply_to=cleaned_data.get("reply_to"),
            post_id=self.post.pk,
            instance_pk=self.instance.pk,
        )

        if errors:
            raise ValidationError(errors)

        return cleaned_data


class CommentUpdateForm(forms.ModelForm):
    """
    Форма редактирования существующего комментария.
    """

    class Meta:
        model = Comment
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(
                attrs={"class": "form-control", "placeholder": "Комментарий...", "rows": 5}
            ),
        }

    def clean(self):
        """
        Валидация, что обновленный комментарий не пустой.
        """
        cleaned_data = super().clean()
        content = cleaned_data.get("content")
        if not content or not content.strip():
            self.add_error("content", "Комментарий не может быть пустым.")
        return cleaned_data
