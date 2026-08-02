from types import SimpleNamespace

import pytest
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from posts.api.serializers import CommentSerializer, PostSerializer


class TestPostSerializer:
    """Тестирование сериализатора постов."""

    def test_get_time_update(self):
        """
        Проверка возвращения времени изменения в локальном часовом поясе при редактировании поста,
        если пост не редактировался, возвращает None.
        """
        now = timezone.now()
        post_edited = SimpleNamespace(is_edited=True, time_update=now)
        post_not_edited = SimpleNamespace(is_edited=False, time_update=now)

        serializer = PostSerializer()

        assert serializer.get_time_update(post_edited) == timezone.localtime(now).isoformat()
        assert serializer.get_time_update(post_not_edited) is None

    def test_can_edit_or_delete_unauthenticated(self):
        """Неавторизованный пользователь не может редактировать пост."""
        mock_request = SimpleNamespace(user=SimpleNamespace(is_authenticated=False))
        serializer = PostSerializer(context={"request": mock_request})

        assert serializer.get_can_edit_or_delete(SimpleNamespace()) is False

    def test_can_edit_or_delete_authenticated(self, mocker):
        """
        Для авторизованного пользователя права на редактирование поста
        проверяются через сервисную функцию, разрешено автору или модератору.
        """
        mock_user = SimpleNamespace(is_authenticated=True)
        mock_request = SimpleNamespace(user=mock_user)
        mock_post = SimpleNamespace()

        mock_is_author = mocker.patch(
            "posts.api.serializers.is_author_or_moderator", return_value=True
        )

        serializer = PostSerializer(context={"request": mock_request})

        assert serializer.get_can_edit_or_delete(mock_post) is True
        mock_is_author.assert_called_once_with(
            user=mock_user, obj=mock_post, permission_required="posts.moderate_post"
        )

    def test_validate_tags_calls_service(self, mocker):
        """Нормализация тегов."""
        mock_validate = mocker.patch(
            "posts.api.serializers.validate_and_normalize_tags", return_value=["django"]
        )
        serializer = PostSerializer()

        result = serializer.validate_tags(["Django "])

        mock_validate.assert_called_once_with(["Django "])
        assert result == ["django"]

    def test_create_assigns_tags(self, mocker):
        """Метод create корректно извлекает теги и устанавливает их."""
        serializer = PostSerializer()
        mock_post = mocker.Mock()
        mock_super_create = mocker.patch(
            "rest_framework.serializers.ModelSerializer.create", return_value=mock_post
        )

        serializer.create({"title": "Новый пост", "tags": ["python", "django"]})

        # Теги удалены из kwargs
        mock_super_create.assert_called_once_with({"title": "Новый пост"})
        # Теги присвоены через .set()
        mock_post.tags.set.assert_called_once_with(["python", "django"])

    def test_update_assigns_tags(self, mocker):
        """Метод update корректно обновляет теги, если они переданы."""
        serializer = PostSerializer()
        mock_instance = mocker.Mock()
        mock_super_update = mocker.patch(
            "rest_framework.serializers.ModelSerializer.update", return_value=mock_instance
        )

        serializer.update(mock_instance, {"title": "Обновлено", "tags": ["drf"]})

        mock_super_update.assert_called_once_with(mock_instance, {"title": "Обновлено"})
        mock_instance.tags.set.assert_called_once_with(["drf"])


class TestCommentSerializer:
    """Тестирование сериализатора комментариев."""

    def test_read_only_fields_on_update(self):
        """
        При обновлении поля иерархии комментария (parent_comment и reply_to)
        блокируются от изменений.
        """
        mock_instance = SimpleNamespace(pk=1)

        # При редактировании поля становятся read_only
        serializer_update = CommentSerializer(instance=mock_instance)
        assert serializer_update.fields["parent_comment"].read_only is True
        assert serializer_update.fields["reply_to"].read_only is True

        # При создании остаются редактируемыми
        serializer_create = CommentSerializer()
        assert serializer_create.fields["parent_comment"].read_only is False
        assert serializer_create.fields["reply_to"].read_only is False

    def test_get_child_comments_conditions(self, mocker):
        """
        Дочерние комментарии обрабатываются только для родительских комментариев
        при флаге display_tree=True (передается в context сериализатора из api view).
        """
        serializer_no_tree = CommentSerializer(context={"display_tree": False})
        serializer_with_tree = CommentSerializer(context={"display_tree": True})

        child_comment = SimpleNamespace(parent_comment_id=1, child_comments=["mock"])
        parent_comment = SimpleNamespace(parent_comment_id=None, child_comments=["mock"])

        # Если комментарий является дочерним — возвращается None, а не список дочерних комментариев
        assert serializer_with_tree.get_child_comments(child_comment) is None

        # Если это родительский комментарий, но флага в context нет — возвращается None
        assert serializer_no_tree.get_child_comments(parent_comment) is None

        # CommentSerializer заменяется на MagicMock
        mock_serializer_cls = mocker.patch("posts.api.serializers.CommentSerializer")
        # mock_serializer_cls.return_value - то, что вернется при вызове класса - MagicMock
        # .data - у вернувшегося MagicMock задается атрибут .data с нужным значением,
        # у настоящего CommentSerializer .data - это @property
        mock_serializer_cls.return_value.data = ["serialized_child_comment"]

        result = serializer_with_tree.get_child_comments(parent_comment)

        assert result == ["serialized_child_comment"]
        mock_serializer_cls.assert_called_once_with(
            parent_comment.child_comments,
            many=True,
            context=serializer_with_tree.context,
        )

    def test_get_children_count(self):
        """Количество ответов возвращается только для родительских комментариев."""
        serializer = CommentSerializer()

        comment_root_with_count = SimpleNamespace(parent_comment_id=None, children_count=5)
        comment_child_with_count = SimpleNamespace(parent_comment_id=1, children_count=5)
        comment_no_count = SimpleNamespace(parent_comment_id=None)

        assert serializer.get_children_count(comment_root_with_count) == 5
        assert serializer.get_children_count(comment_child_with_count) is None
        assert serializer.get_children_count(comment_no_count) is None

    def test_validate_hierarchy_calls_service(self, mocker):
        """Проверка вызова сервиса validate_comment при валидации."""
        mock_validate = mocker.patch(
            "posts.api.serializers.validate_comment",
            return_value={"reply_to": ["Для дочернего комментария необходимо указать reply_to."]},
        )
        mock_post = SimpleNamespace(pk=5)
        serializer = CommentSerializer(context={"post": mock_post})

        with pytest.raises(ValidationError) as exc:
            serializer.validate({"content": "Текст", "parent_comment": 1, "reply_to": 2})

        assert "reply_to" in exc.value.detail
        mock_validate.assert_called_once_with(
            content="Текст", parent_comment=1, reply_to=2, post_id=mock_post.pk, instance_pk=None
        )
