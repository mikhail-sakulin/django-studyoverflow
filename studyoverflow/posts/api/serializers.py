from django.contrib.auth import get_user_model
from django.utils.timezone import localtime
from posts.models import Post
from posts.services import validate_and_normalize_tags
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
