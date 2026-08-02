from types import SimpleNamespace

import pytest
from django.core.exceptions import ValidationError

from posts.services import (
    PostTitleValidator,
    validate_and_normalize_tags,
    validate_comment,
)


class TestPostTitleValidator:
    MIN_LEN = 10
    MAX_LEN = 30

    @pytest.fixture
    def validator(self):
        return PostTitleValidator(min_len=self.MIN_LEN, max_len=self.MAX_LEN)

    def test_valid_title(self, validator):
        """Заголовок допустимой длины."""
        validator("а" * self.MIN_LEN)
        validator("а" * (self.MIN_LEN + 1))
        validator("а" * self.MAX_LEN)

    def test_title_too_short(self, validator):
        """Слишком короткий заголовок вызывает ValidationError."""
        with pytest.raises(ValidationError) as exc:
            validator("а" * (self.MIN_LEN - 1))

        assert exc.value.code == "title_too_short"
        assert f"не менее {self.MIN_LEN} символов" in exc.value.messages[0]

    def test_title_too_long(self, validator):
        """Слишком длинный заголовок вызывает ValidationError."""
        with pytest.raises(ValidationError) as exc:
            validator("а" * (self.MAX_LEN + 1))

        assert exc.value.code == "title_too_long"
        assert f"не более {self.MAX_LEN} символов" in exc.value.messages[0]


class TestValidateAndNormalizeTags:
    @pytest.fixture(autouse=True)
    def mock_normalize(self, mocker):
        # side_effect умеет принимать передаваемые в mock значения
        return mocker.patch(
            "posts.services.validators.normalize_tag_name",
            side_effect=lambda tag: tag.strip().lower(),
        )

    def test_valid_tags_are_normalized(self):
        """Корректный список тегов успешно нормализуется и возвращается."""
        result = validate_and_normalize_tags([" Tag1 ", "TAG2"])
        assert result == ["tag1", "tag2"]

    def test_empty_tags_raises_error(self):
        """Пустой список вызывает ошибку, нужен хотя бы 1 тег."""
        with pytest.raises(ValidationError) as exc:
            validate_and_normalize_tags([])
        assert exc.value.code == "too_few_tags"

    def test_too_many_tags_raises_error(self):
        """Если тегов больше 10 (max числа), то вызывается ошибка."""
        tags = [f"tag{i}" for i in range(11)]
        with pytest.raises(ValidationError) as exc:
            validate_and_normalize_tags(tags)
        assert exc.value.code == "too_many_tags"

    def test_tag_too_long_after_normalization(self, mocker):
        """Если после нормализации тег больше 50 символов, вызывается ошибка."""
        mocker.patch("posts.services.validators.normalize_tag_name", return_value="a" * 51)

        # match проверяет текст сообщения исключения
        with pytest.raises(ValidationError, match="Длина тега не может превышать 50 символов."):
            validate_and_normalize_tags(["some_tag"])


class TestValidateComment:
    """Тесты validate_comment валидации иерархии комментариев."""

    @pytest.fixture
    def base_kwargs(self):
        """Базовые валидные данные для создания корневого комментария."""
        return {
            "content": "Valid comment.",
            "parent_comment": None,
            "reply_to": None,
            "post_id": 1,
            "instance_pk": None,
        }

    def test_valid_root_comment(self, base_kwargs):
        """Успешная валидация корневого комментария."""
        errors = validate_comment(**base_kwargs)
        assert not errors

    @pytest.mark.parametrize("invalid_content", ["", "   ", None])
    def test_invalid_content(self, base_kwargs, invalid_content):
        """Пустой или состоящий только из пробелов контент вызывает ошибку."""
        base_kwargs["content"] = invalid_content
        errors = validate_comment(**base_kwargs)

        assert "content" in errors
        assert errors["content"] == "Комментарий не может быть пустым."

    def test_missing_reply_to(self, base_kwargs):
        """Указан родитель, но не указан комментарий для ответа."""
        base_kwargs["parent_comment"] = SimpleNamespace(pk=1, post_id=1)
        errors = validate_comment(**base_kwargs)

        assert errors["reply_to"] == "Для дочернего комментария необходимо указать reply_to."

    def test_missing_parent_comment(self, base_kwargs):
        """Указан комментарий для ответа, но отсутствует родитель ветки."""
        base_kwargs["reply_to"] = SimpleNamespace(pk=1, post_id=1)
        errors = validate_comment(**base_kwargs)

        assert errors["parent_comment"] == "Для ответа необходимо указать parent_comment."

    def test_circular_parent_reference(self, base_kwargs):
        """Комментарий ссылается на себя же как на родителя (parent_comment)."""
        base_kwargs.update(
            {
                "instance_pk": 5,
                "parent_comment": SimpleNamespace(pk=5, post_id=1),
                "reply_to": SimpleNamespace(pk=2, post_id=1, parent_comment_id=5),
            }
        )
        errors = validate_comment(**base_kwargs)

        assert errors["parent_comment"] == "Комментарий не может быть родителем сам себе."

    def test_circular_reply_reference(self, base_kwargs):
        """Комментарий пытается ответить самому себе (reply_to)."""
        base_kwargs.update(
            {
                "instance_pk": 5,
                "parent_comment": SimpleNamespace(pk=1, post_id=1),
                "reply_to": SimpleNamespace(pk=5, post_id=1, parent_comment_id=1),
            }
        )
        errors = validate_comment(**base_kwargs)

        assert errors["reply_to"] == "Комментарий не может отвечать сам себе."

    def test_wrong_post_relations(self, base_kwargs):
        """parent_comment и reply_to принадлежат другому посту."""
        base_kwargs.update(
            {
                "parent_comment": SimpleNamespace(pk=1, post_id=99),
                "reply_to": SimpleNamespace(pk=2, post_id=99, parent_comment_id=1),
            }
        )
        errors = validate_comment(**base_kwargs)

        assert errors["parent_comment"] == "Родительский комментарий принадлежит другому посту."
        assert errors["reply_to"] == "Комментарий для ответа принадлежит другому посту."

    def test_reply_to_wrong_branch(self, base_kwargs):
        """
        reply_to относится к другой ветке, его parent_comment_id не совпадает с parent_comment.pk
        """
        base_kwargs.update(
            {
                "parent_comment": SimpleNamespace(pk=1, post_id=1),
                "reply_to": SimpleNamespace(pk=3, post_id=1, parent_comment_id=99),
            }
        )
        errors = validate_comment(**base_kwargs)

        assert errors["reply_to"] == "Неверный комментарий для ответа (другая ветка)."

    def test_reply_to_unrelated_root(self, base_kwargs):
        """
        reply_to является корневым комментарием (parent_comment_id == None),
        но не тем же самым, что указан в parent_comment.
        """
        base_kwargs.update(
            {
                "parent_comment": SimpleNamespace(pk=1, post_id=1),
                "reply_to": SimpleNamespace(pk=2, post_id=1, parent_comment_id=None),
            }
        )
        errors = validate_comment(**base_kwargs)

        assert errors["reply_to"] == "Ответ должен ссылаться на корень ветки или его детей."

    def test_valid_reply_to_root(self, base_kwargs):
        """Успешный ответ на корневой комментарий."""
        root = SimpleNamespace(pk=1, post_id=1, parent_comment_id=None)
        base_kwargs.update(
            {
                "parent_comment": root,
                "reply_to": root,
            }
        )
        errors = validate_comment(**base_kwargs)

        assert not errors

    def test_valid_reply_to_child(self, base_kwargs):
        """Успешный ответ на дочерний комментарий внутри правильной ветки."""
        base_kwargs.update(
            {
                "parent_comment": SimpleNamespace(pk=1, post_id=1),
                "reply_to": SimpleNamespace(pk=2, post_id=1, parent_comment_id=1),
            }
        )
        errors = validate_comment(**base_kwargs)

        assert not errors
