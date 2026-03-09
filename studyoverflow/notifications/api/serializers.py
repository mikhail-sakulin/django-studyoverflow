from django.contrib.auth import get_user_model
from notifications.models import Notification
from posts.models import Like
from rest_framework import serializers


User = get_user_model()


class ActorSerializer(serializers.ModelSerializer):
    """
    Сериализатор для краткого отображения данных инициатора уведомления.
    """

    class Meta:
        model = User
        fields = ("id", "username", "avatar")


class NotificationSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source="get_notification_type_display", read_only=True)
    actor = ActorSerializer()
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

    def get_content_object_url(self, notification):
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
