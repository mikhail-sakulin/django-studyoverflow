from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from posts.models import MAX_NAME_LENGTH_TAG, MAX_TITLE_SLUG_LENGTH_POST, Comment, Post
from taggit.forms import TagWidget
from users.services.infrastructure import CustomUsernameValidator


class PostCreateForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "content", "tags"]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Введите заголовок"}
            ),
            "content": forms.Textarea(
                attrs={"class": "form-control", "placeholder": "Введите содержимое...", "rows": 5}
            ),
            "tags": TagWidget(attrs={"class": "form-control", "placeholder": "Введите теги..."}),
        }

    def clean_title(self):
        title = self.cleaned_data["title"]

        if len(title) < 10:
            raise ValidationError("Длина заголовка должна быть не менее 10 символов")

        if len(title) > MAX_TITLE_SLUG_LENGTH_POST:
            raise ValidationError(
                f"Длина заголовка должна быть не более {MAX_NAME_LENGTH_TAG} символов"
            )

        return title

    def clean_tags(self):
        tags_list = self.cleaned_data["tags"]

        if len(tags_list) == 0:
            raise ValidationError("Укажите хотя бы 1 тег.")

        if len(tags_list) > 10:
            raise ValidationError("Укажите не более 10 тегов.")

        for el in tags_list:
            if len(el) > MAX_NAME_LENGTH_TAG:
                raise ValidationError(
                    f"Длина тега не может превышать {MAX_NAME_LENGTH_TAG} символов."
                )

        return tags_list


class PostFilterForm(forms.Form):
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
        self.user = kwargs.pop("user", None)
        self.post = kwargs.pop("post", None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        parent_comment = cleaned_data.get("parent_comment")
        reply_to = cleaned_data.get("reply_to")

        errors = {}

        # Проверка принадлежности parent_comment посту
        if parent_comment and parent_comment.post != self.post:
            errors["parent_comment"] = ValidationError(
                "Родительский комментарий не принадлежит этому посту."
            )

        # Проверка на комментирование своего поста
        if self.user == self.post.author and not parent_comment:
            errors["content"] = ValidationError(
                "Вы не можете комментировать свой собственный пост."
            )

        # Проверка reply_to
        if reply_to:
            if reply_to.post != self.post:
                errors["reply_to"] = ValidationError(
                    "Комментарий для ответа не принадлежит этому посту."
                )

            if self.user == reply_to.author:
                errors["reply_to"] = ValidationError("Вы не можете отвечать на свой комментарий.")

        if errors:
            raise ValidationError(errors)

        return cleaned_data


class CommentUpdateForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(
                attrs={"class": "form-control", "placeholder": "Комментарий...", "rows": 5}
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        content = cleaned_data.get("content")
        if not content or not content.strip():
            self.add_error("content", "Комментарий не может быть пустым.")
        return cleaned_data
