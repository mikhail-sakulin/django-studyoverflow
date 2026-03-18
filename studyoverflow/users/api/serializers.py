from django.contrib.auth import get_user_model
from rest_framework import serializers
from users.services import is_user_online


User = get_user_model()


class UserPublicProfileSerializer(serializers.ModelSerializer):
    """
    Сериализатор для публичного профиля пользователя.

    Предоставляет общую информацию, доступную всем посетителям, включая
    статус "онлайн" и ссылки на различные размеры аватара.
    """

    avatar_urls = serializers.SerializerMethodField()
    online_status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "role",
            "online_status",
            "avatar_urls",
            "first_name",
            "last_name",
            "bio",
            "reputation",
            "posts_count",
            "comments_count",
            "date_birth",
            "date_joined",
            "last_seen",
            "is_blocked",
        ]
        read_only_fields = fields

    def get_avatar_urls(self, user):
        """Возвращает словарь ссылок на оригинал и миниатюры аватара."""
        return {
            "avatar_original": user.avatar.url,
            "size1": user.avatar_small_size1_url,
            "size2": user.avatar_small_size2_url,
            "size3": user.avatar_small_size3_url,
        }

    def get_online_status(self, user):
        """Проверяет текущий статус активности пользователя в Redis."""
        return is_user_online(user.pk)


class UserMyProfileSerializer(UserPublicProfileSerializer):
    """
    Сериализатор для профиля текущего авторизованного пользователя.

    Расширяет публичный профиль приватными полями и возможностью загрузки аватара.
    """

    class Meta(UserPublicProfileSerializer.Meta):
        fields = UserPublicProfileSerializer.Meta.fields + ["is_social", "avatar"]
        extra_kwargs = {
            "avatar": {"write_only": True},
        }
        read_only_fields = [
            "id",
            "avatar_urls",
            "reputation",
            "posts_count",
            "comments_count",
            "date_joined",
            "last_seen",
            "is_social",
            "role",
            "is_blocked",
        ]


class UserListSerializer(serializers.ModelSerializer):
    """
    Сериализатор для краткого отображения списка пользователей.
    """

    avatar_url = serializers.CharField(source="avatar_small_size2_url")
    online_status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "role",
            "online_status",
            "avatar_url",
            "reputation",
            "posts_count",
            "comments_count",
            "last_seen",
        ]
        read_only_fields = fields

    def get_online_status(self, user):
        """
        Определяет статус онлайн на основе списка ID, полученного из контекста из Redis во ViewSet.
        """
        online_ids = self.context.get("online_ids", set())
        return user.id in online_ids
