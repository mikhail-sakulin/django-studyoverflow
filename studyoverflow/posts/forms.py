from django import forms
from django.core.exceptions import ValidationError
from posts.models import MAX_NAME_SLUG_LENGTH_TAG, MAX_TITLE_SLUG_LENGTH_POST, Comment, Post
from taggit.forms import TagWidget


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
            "tags": TagWidget(attrs={"class": "form-control", "placeholder": "Введите теги"}),
        }

    def clean_title(self):
        title = self.cleaned_data["title"]

        if len(title) < 10:
            raise ValidationError("Длина заголовка должна быть не менее 10 символов")

        if len(title) > MAX_TITLE_SLUG_LENGTH_POST:
            raise ValidationError(
                f"Длина заголовка должна быть не более {MAX_NAME_SLUG_LENGTH_TAG} символов"
            )

        return title

    def clean_tags(self):
        tags_list = self.cleaned_data["tags"]

        if len(tags_list) == 0:
            raise ValidationError("Укажите хотя бы 1 тег.")

        if len(tags_list) > 10:
            raise ValidationError("Укажите не более 10 тегов.")

        for el in tags_list:
            if len(el) > MAX_NAME_SLUG_LENGTH_TAG:
                raise ValidationError(
                    f"Длина тега не может превышать {MAX_NAME_SLUG_LENGTH_TAG} символов."
                )

        return tags_list


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

    def clean_parent_comment(self):
        parent_comment = self.cleaned_data["parent_comment"]
        if parent_comment:
            post = self.post
            if parent_comment.post != post:
                raise ValidationError(
                    "Указанный родительский комментарий не принадлежит этому посту."
                )
        return parent_comment

    def clean_reply_to(self):
        reply_to = self.cleaned_data["reply_to"]
        parent_comment = self.cleaned_data["parent_comment"]
        if reply_to and parent_comment:
            if reply_to.post != self.post:
                raise ValidationError("Комментарий для ответа не принадлежит этому посту.")

            if reply_to.parent_comment is not None and reply_to.parent_comment != parent_comment:
                raise ValidationError("Указан неверный комментарий для ответа.")

        return reply_to
