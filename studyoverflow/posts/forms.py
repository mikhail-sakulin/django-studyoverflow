from django import forms
from django.core.exceptions import ValidationError
from posts.models import Post


class PostCreateForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "content"]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Введите заголовок"}
            ),
            "content": forms.Textarea(
                attrs={"class": "form-control", "placeholder": "Введите содержимое...", "rows": 5}
            ),
        }

    def clean_title(self):
        title = self.cleaned_data["title"]

        if len(title) < 10:
            raise ValidationError("Длина заголовка должна быть не менее 10 символов")

        if len(title) > 255:
            raise ValidationError("Длина заголовка должна быть не более 255 символов")

        return title
