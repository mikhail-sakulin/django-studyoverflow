from django.contrib.auth import get_user_model
from django.utils.timezone import localtime
from posts.models import Comment, Post
from posts.services import validate_and_normalize_tags, validate_comment
from rest_framework import serializers
from taggit.serializers import TagListSerializerField
from users.services import is_author_or_moderator


User = get_user_model()


class AuthorSerializer(serializers.ModelSerializer):
    """
    Сериализатор для краткого отображения данных автора поста или комментария.
    """

    class Meta:
        model = User
        fields = ("id", "username", "avatar")


class PostSerializer(serializers.ModelSerializer):
    """
    Сериализатор для постов.

    Включает агрегацию лайков, комментариев и валидацию, нормализацию и назначение тегов.
    """

    author = AuthorSerializer(read_only=True)
    time_update = serializers.SerializerMethodField()
    content = serializers.CharField(write_only=True, required=False, allow_blank=True)
    tags = TagListSerializerField()

    # Аннотированные поля, должны добавляться в queryset
    likes_count = serializers.IntegerField(read_only=True, default=0)
    user_has_liked = serializers.BooleanField(read_only=True, default=False)
    comments_count = serializers.IntegerField(read_only=True, default=0)

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

    def get_time_update(self, post):
        """Возвращает время изменения в локальном часовом поясе, если пост редактировался."""
        if post.is_edited and post.time_update:
            # перевод времени UTC из базы в зону, указанную в settings.TIME_ZONE
            return localtime(post.time_update).isoformat()
        return None

    def get_can_edit_or_delete(self, post):
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


class CommentSerializer(serializers.ModelSerializer):
    """
    Сериализатор для комментариев.

    Поддерживает вложенную структуру, включает агрегацию лайков и дочерних комментариев.
    """

    author = AuthorSerializer(read_only=True)
    time_update = serializers.SerializerMethodField()
    content = serializers.CharField(write_only=True, required=True)

    # Аннотированные поля, должны добавляться в queryset
    likes_count = serializers.IntegerField(read_only=True, default=0)
    user_has_liked = serializers.BooleanField(read_only=True, default=False)

    # Флаг может ли текущий пользователь изменять или удалять объект
    can_edit_or_delete = serializers.SerializerMethodField()

    # Счетчик дочерних комментариев. Считается только для родительских комментариев.
    children_count = serializers.SerializerMethodField()

    # Вложенность через "self"
    child_comments = serializers.SerializerMethodField()

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
        fields = (
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
            "children_count",
            "child_comments",
        )
        read_only_fields = (
            "id",
            "author",
            "time_create",
            "is_edited",
            "time_update",
            "rendered_content",
            "likes_count",
            "user_has_liked",
            "can_edit_or_delete",
            "children_count",
            "child_comments",
        )

    def __init__(self, *args, **kwargs):
        """Блокирует возможность изменения parent_comment или reply_to при редактировании."""
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields["parent_comment"].read_only = True
            self.fields["reply_to"].read_only = True

    def get_time_update(self, comment):
        """Возвращает время изменения в локальном часовом поясе, если комментарий редактировался."""
        if comment.is_edited and comment.time_update:
            # перевод времени UTC из базы в зону, указанную в settings.TIME_ZONE
            return localtime(comment.time_update).isoformat()
        return None

    def get_can_edit_or_delete(self, comment):
        """Возвращает флаг, может ли текущий пользователь изменять или удалять объект."""
        user = self.context["request"].user
        if not user.is_authenticated:
            return False

        return is_author_or_moderator(
            user=user, obj=comment, permission_required="posts.moderate_comment"
        )

    def get_child_comments(self, comment):
        """
        Отображает вложенные (child) комментарии тем же сериализатором:
        - Возвращает данные только для родительских комментариев (parent_comment is None).
        - Использует флаг 'display_tree' из context для отображения дочерних комментариев.
        """
        if comment.parent_comment_id is not None:
            return None

        if not self.context.get("display_tree", False):
            return None

        if comment.child_comments:
            return CommentSerializer(comment.child_comments, many=True, context=self.context).data
        return None

    def get_children_count(self, comment):
        """Количество дочерних комментариев для родительского. Возвращает None для дочерних."""
        if comment.parent_comment_id is not None:
            return None

        return comment.children_count

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
