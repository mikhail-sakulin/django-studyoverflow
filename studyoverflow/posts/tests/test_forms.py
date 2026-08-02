import pytest
from django.core.exceptions import ValidationError

from posts.forms import CommentCreateForm, CommentUpdateForm, PostCreateForm, PostFilterForm


@pytest.mark.django_db
class TestPostCreateForm:
    def test_valid_form(self, mocker):
        """Успешная валидация формы с вызовом нормализации тегов."""
        mocker.patch(
            "posts.forms.validate_and_normalize_tags",
            return_value=["python", "django"],
        )
        form = PostCreateForm(
            data={
                "title": "Тестовый заголовок",
                "content": "Тестовый контент поста.",
                "tags": "python, django",
            }
        )
        assert form.is_valid()
        assert form.cleaned_data["tags"] == ["python", "django"]

    def test_invalid_tags_raises_error(self, mocker):
        """Ошибка валидации при некорректных тегах от сервиса."""
        mocker.patch(
            "posts.forms.validate_and_normalize_tags",
            side_effect=ValidationError("Некорректный тег"),
        )
        form = PostCreateForm(
            data={
                "title": "Заголовок",
                "content": "Контент",
                "tags": "invalid_tag",
            }
        )
        assert not form.is_valid()
        assert "tags" in form.errors


@pytest.mark.django_db
class TestPostFilterForm:
    def test_empty_author_is_valid(self):
        """Пустая строка автора считается валидной и очищается."""
        form = PostFilterForm(data={"author": "   "})
        assert form.is_valid()
        assert form.cleaned_data["author"] == ""

    def test_existing_author_is_valid(self, user_factory):
        """Существующий пользователь без учета регистра проходит валидацию."""
        user_factory(username="valid_author")
        form = PostFilterForm(data={"author": "VALID_AUTHOR"})
        assert form.is_valid()
        assert form.cleaned_data["author"] == "VALID_AUTHOR"

    def test_nonexistent_author_is_invalid(self):
        """Несуществующий пользователь вызывает ошибку валидации."""
        form = PostFilterForm(data={"author": "ghost_user"})
        assert not form.is_valid()
        assert "author" in form.errors
        assert "Указанного автора не существует." in form.errors["author"]


@pytest.mark.django_db
class TestCommentCreateForm:
    def test_valid_comment_creation(self, user_factory, post_factory, mocker):
        """Передача user и post в kwargs и успешная валидация."""
        user = user_factory()
        post = post_factory()
        mocker.patch("posts.forms.validate_comment", return_value={})

        form = CommentCreateForm(
            data={"content": "Комментарий к посту."},
            user=user,
            post=post,
        )
        assert form.is_valid()

    def test_invalid_comment_hierarchy_raises_errors(
        self, user_factory, post_factory, comment_factory, mocker
    ):
        """Ошибки из функции validate_comment пробрасываются в ошибки формы."""
        user = user_factory()
        post = post_factory()
        parent_comment = comment_factory(post=post)
        mocker.patch(
            "posts.forms.validate_comment",
            return_value={"reply_to": ["Для дочернего комментария необходимо указать reply_to."]},
        )

        form = CommentCreateForm(
            data={"content": "Ответ", "parent_comment": parent_comment.id},
            user=user,
            post=parent_comment.post,
        )
        assert not form.is_valid()
        assert "reply_to" in form.errors


class TestCommentUpdateForm:
    def test_valid_content_update(self):
        """Успешное обновление с непустым контентом."""
        form = CommentUpdateForm(data={"content": "Обновленный текст"})
        assert form.is_valid()

    @pytest.mark.parametrize("invalid_content", ["", "   ", None])
    def test_empty_content_is_invalid(self, invalid_content):
        """Пустой контент или контент из пробелов вызывает ошибку."""
        form = CommentUpdateForm(data={"content": invalid_content})
        assert not form.is_valid()
        assert "content" in form.errors
        assert "Комментарий не может быть пустым." in form.errors["content"]
