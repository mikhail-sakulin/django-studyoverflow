from notifications.api.serializers import NotificationSerializer
from notifications.mixins import NotificationOptimizeMixin
from notifications.models import Notification
from notifications.tasks import send_channel_notify_event
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


class NotificationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    NotificationOptimizeMixin,
    viewsets.GenericViewSet,
):

    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        queryset = Notification.objects.filter(user=self.request.user)
        return self.optimize_notification_queryset(queryset)

    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        """Возвращает количество непрочитанных уведомлений."""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({"unread_count": count})

    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request):
        """
        Помечает все непрочитанные уведомления пользователя прочитанными и создает
        Celery задачу для обновления счетчика непрочитанных уведомлений через Channels WebSocket.
        """
        self.get_queryset().filter(is_read=False).update(is_read=True)

        send_channel_notify_event.delay(user_id=request.user.pk, update_list=False)

        return Response({"status": "all notifications marked as read"})

    @action(detail=True, methods=["patch"], url_path="mark-read")
    def mark_read(self, request, pk=None):
        """Помечает одно уведомление прочитанным."""
        notification = self.get_object()
        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=["is_read"])
        return Response({"status": "notification marked as read"})

    @action(detail=False, methods=["delete"], url_path="delete-all")
    def delete_all(self, request):
        """Удаляет все уведомления пользователя"""
        self.get_queryset().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
