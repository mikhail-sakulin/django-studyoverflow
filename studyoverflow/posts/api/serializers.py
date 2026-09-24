from django.contrib.auth import get_user_model
from django.utils.timezone import localtime
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from taggit.serializers import TagListSerializerField

from posts.models import Comment, LowercaseTag, Post
from posts.services.validators import (
    validate_and_normalize_tags,
    validate_author_exists,
    validate_comment,
    validate_search_query,
)
from users.api.serializers import AvatarSerializer
from users.services.permissions import is_author_or_moderator


User = get_user_model()


class AuthorSerializer(serializers.ModelSerializer):
    """
    Сериализатор для краткого отображения данных автора поста или комментария.
    """

    avatars = AvatarSerializer(source="*", read_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "avatars")


class PostSerializer(serializers.ModelSerializer):
    """
    Сериализатор для постов.

    Включает агрегацию лайков, комментариев и валидацию, нормализацию и назначение тегов.
    """

    author = AuthorSerializer(read_only=True)
    time_update = serializers.SerializerMethodField()
    title = serializers.CharField(
        min_length=Post.MIN_TITLE_LENGTH,
        max_length=Post.MAX_TITLE_SLUG_LENGTH_POST,
        required=True,
        error_messages={
            "max_length": f"Длина заголовка не должна превышать "
            f"{Post.MAX_TITLE_SLUG_LENGTH_POST} символов."
        },
    )
    content = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        max_length=Post.MAX_CONTENT_LENGTH,
        error_messages={
            "max_length": f"Длина контента не должна превышать {Post.MAX_CONTENT_LENGTH} символов."
        },
    )
    tags = TagListSerializerField()
    likes_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)

    # Аннотированное поля, лайкнул ли пользователь пост, должно добавляться в queryset
    user_has_liked = serializers.BooleanField(read_only=True, default=False)

    # Флаг может ли текущий пользователь изменять или удалять объект
    can_edit_or_delete = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = (
            "id",
            "author",
            "time_create",
            "is_edited",
            "time_update",
            "title",
            "slug",
            "content",
            "rendered_content",
            "tags",
            "likes_count",
            "user_has_liked",
            "comments_count",
            "can_edit_or_delete",
        )
        read_only_fields = (
            "id",
            "author",
            "time_create",
            "is_edited",
            "time_update",
            "slug",
            "rendered_content",
            "likes_count",
            "user_has_liked",
            "comments_count",
            "can_edit_or_delete",
        )

    @extend_schema_field(serializers.DateTimeField(allow_null=True))
    def get_time_update(self, post) -> str | None:
        """Возвращает время изменения в локальном часовом поясе, если пост редактировался."""
        if post.is_edited and post.time_update:
            # перевод времени UTC из базы в зону, указанную в settings.TIME_ZONE
            return localtime(post.time_update).isoformat()
        return None

    def get_can_edit_or_delete(self, post) -> bool:
        user = self.context["request"].user
        if not user.is_authenticated:
            return False

        return is_author_or_moderator(
            user=user, obj=post, permission_required="posts.moderate_post"
        )

    def validate_tags(self, value):
        """Валидация и нормализация тегов."""
        return validate_and_normalize_tags(value)

    def create(self, validated_data):
        """Создание поста с последующей установкой Many-to-Many тегов."""
        tags = validated_data.pop("tags", [])
        post = super().create(validated_data)
        post.tags.set(tags)
        return post

    def update(self, instance, validated_data):
        """Обновление поста и синхронизация списка тегов."""
        tags = validated_data.pop("tags", None)
        instance = super().update(instance, validated_data)
        if tags is not None:
            instance.tags.set(tags)
        return instance


class PostFilterSerializer(serializers.Serializer):
    """Сериализатор для валидации GET-параметров фильтрации списка постов."""

    q = serializers.CharField(required=False, allow_blank=True)
    author = serializers.CharField(required=False, allow_blank=True)

    def validate_q(self, value: str) -> str:
        return validate_search_query(value)

    def validate_author(self, value: str) -> str:
        return validate_author_exists(value)


class CommentBaseSerializer(serializers.ModelSerializer):
    """
    Базовый сериализатор для комментариев без информации о вложенности.
    """

    author = AuthorSerializer(read_only=True)
    time_update = serializers.SerializerMethodField()
    content = serializers.CharField(
        write_only=True,
        required=True,
        max_length=Comment.MAX_CONTENT_LENGTH,
        error_messages={
            "max_length": f"Длина комментария не должна превышать "
            f"{Comment.MAX_CONTENT_LENGTH} символов."
        },
    )
    likes_count = serializers.IntegerField(read_only=True)

    # Аннотированное поля, лайкнул ли пользователь комментарий, должно добавляться в queryset
    user_has_liked = serializers.BooleanField(read_only=True, default=False)

    # Флаг может ли текущий пользователь изменять или удалять объект
    can_edit_or_delete = serializers.SerializerMethodField()

    # Переопределение ForeignKey полей для замены выпадающего списка select
    # на обычное поле ввода для уменьшения нагрузки на БД при работе с UI DRF.
    parent_comment = serializers.PrimaryKeyRelatedField(
        queryset=Comment.objects.all(),
        style={"base_template": "input.html"},
        required=False,
        allow_null=True,
    )
    reply_to = serializers.PrimaryKeyRelatedField(
        queryset=Comment.objects.all(),
        style={"base_template": "input.html"},
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Comment
        fields: tuple[str, ...] = (
            "id",
            "author",
            "parent_comment",
            "reply_to",
            "time_create",
            "is_edited",
            "time_update",
            "content",
            "rendered_content",
            "likes_count",
            "user_has_liked",
            "can_edit_or_delete",
        )
        read_only_fields: tuple[str, ...] = (
            "id",
            "author",
            "time_create",
            "is_edited",
            "time_update",
            "rendered_content",
            "likes_count",
            "user_has_liked",
            "can_edit_or_delete",
        )

    def __init__(self, *args, **kwargs):
        """Блокирует возможность изменения parent_comment или reply_to при редактировании."""
        super().__init__(*args, **kwargs)
        if self.instance is not None:
            self.fields["parent_comment"].read_only = True
            self.fields["reply_to"].read_only = True

    @extend_schema_field(serializers.DateTimeField(allow_null=True))
    def get_time_update(self, comment) -> str | None:
        """Возвращает время изменения в локальном часовом поясе, если комментарий редактировался."""
        if comment.is_edited and comment.time_update:
            # перевод времени UTC из БД в зону, указанную в settings.TIME_ZONE
            return localtime(comment.time_update).isoformat()

        return None

    def get_can_edit_or_delete(self, comment) -> bool:
        """Возвращает флаг, может ли текущий пользователь изменять или удалять объект."""
        user = self.context["request"].user
        if not user.is_authenticated:
            return False

        return is_author_or_moderator(
            user=user, obj=comment, permission_required="posts.moderate_comment"
        )

    def validate(self, attrs):
        """Валидация иерархии и целостности комментариев."""
        # Извлечение поста, переданного в контекст во viewset
        post_id = self.context["post"].pk

        # Валидация данных комментария и получение словаря ошибок
        errors = validate_comment(
            content=attrs.get("content"),
            parent_comment=attrs.get("parent_comment"),
            reply_to=attrs.get("reply_to"),
            post_id=post_id,
            instance_pk=self.instance.pk if self.instance else None,
        )

        if errors:
            raise serializers.ValidationError(errors)

        return attrs


class ChildCommentSerializer(CommentBaseSerializer):
    """
    Сериализатор дочернего комментария. Своих дочерних комментариев не имеет (только один
    уровень вложенности), поэтому вложенных полей нет.
    """


class CommentSerializer(CommentBaseSerializer):
    """
    Сериализатор родительского комментария с веткой ответов.
    """

    # Счетчик дочерних комментариев
    child_count = serializers.SerializerMethodField()
    # Вложенные дочерние комментарии
    child_comments = serializers.SerializerMethodField()

    class Meta(CommentBaseSerializer.Meta):
        fields: tuple[str, ...] = CommentBaseSerializer.Meta.fields + (
            "child_count",
            "child_comments",
        )
        read_only_fields: tuple[str, ...] = CommentBaseSerializer.Meta.read_only_fields + (
            "child_count",
            "child_comments",
        )

    @extend_schema_field(ChildCommentSerializer(many=True))
    def get_child_comments(self, comment):
        """
        Отображает вложенные (child) комментарии:
        - Возвращает данные только для родительских комментариев (parent_comment is None).
        - Использует флаг 'display_tree' из context для отображения дочерних комментариев.
        """
        if comment.parent_comment_id is not None:
            return None

        if not self.context.get("display_tree", False):
            return None

        return ChildCommentSerializer(comment.child_comments, many=True, context=self.context).data

    @extend_schema_field(serializers.IntegerField())
    def get_child_count(self, comment):
        """Количество дочерних комментариев для родительского. Возвращает None для дочерних."""
        if not hasattr(comment, "child_count"):
            return None

        if comment.parent_comment_id is not None:
            return None

        return comment.child_count


class TagSerializer(serializers.ModelSerializer):
    """
    Сериализатор для тегов.
    """

    posts_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = LowercaseTag
        fields = ["id", "name", "posts_count"]
