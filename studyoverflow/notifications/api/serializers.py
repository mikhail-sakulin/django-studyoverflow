from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from notifications.models import Notification
from posts.models import Like
from users.api.serializers import AvatarSerializer


User = get_user_model()


class ActorSerializer(serializers.ModelSerializer):
    """
    Сериализатор для краткого отображения данных инициатора уведомления.
    """

    avatars = AvatarSerializer(source="*", read_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "avatars")


class NotificationSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели уведомлений. Предоставляет подробную информацию об уведомлении.
    """

    type_display = serializers.CharField(source="get_notification_type_display", read_only=True)
    actor = ActorSerializer(read_only=True)
    content_type = serializers.SlugRelatedField(slug_field="model", read_only=True, allow_null=True)
    content_object_url = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "actor",
            "notification_type",
            "type_display",
            "message",
            "is_read",
            "time_create",
            "object_id",
            "content_type",
            "content_object_url",
        ]
        read_only_fields = (
            "id",
            "actor",
            "notification_type",
            "type_display",
            "message",
            "time_create",
            "object_id",
            "content_type",
            "content_object_url",
        )

    @extend_schema_field(serializers.URLField(allow_null=True))
    def get_content_object_url(self, notification):
        """
        Формирует URL связанного с уведомлением объекта.

        Если уведомление связано с лайком, ссылка формируется на объект, который лайкнули.
        Для остальных объектов используется их метод 'get_absolute_url'.
        """
        target = notification.content_object
        request = self.context.get("request")

        if isinstance(target, Like):
            target = target.content_object

        if not target:
            return None

        try:
            if hasattr(target, "get_absolute_url"):
                path = target.get_absolute_url()
                if request:
                    return request.build_absolute_uri(path)
                return path
        except Exception:
            return None

        return None

    def validate_is_read(self, value):
        """
        Разрешает изменять статус прочтения только на True (прочитано),
        изменять на False запрещено.
        """
        if value is False:
            raise serializers.ValidationError(
                "Уведомление можно только прочитать (задать True для поля is_read). "
                "Вернуть is_read на False нельзя."
            )
        return value
