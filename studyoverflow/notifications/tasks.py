import logging

from asgiref.sync import async_to_sync
from celery_once import QueueOnce
from channels.layers import get_channel_layer
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from notifications.models import Notification

from studyoverflow.celery import app


logger = logging.getLogger(__name__)


@app.task
def create_notification(user_id, actor_id, message, notification_type, content_type_id, object_id):
    """
    Асинхронная Celery задача для создания уведомления Notification.
    """
    with transaction.atomic():
        try:
            content_type = ContentType.objects.get_for_id(content_type_id)
            model_class = content_type.model_class()

            if not model_class.objects.filter(pk=object_id).select_for_update().first():
                return

            Notification.objects.create(
                user_id=user_id,
                actor_id=actor_id,
                message=message,
                notification_type=notification_type,
                content_type_id=content_type_id,
                object_id=object_id,
            )

        except ContentType.DoesNotExist:
            logger.warning(
                f"ContentType с id={content_type_id} не найден.",
                extra={
                    "user_id": user_id,
                    "actor_id": actor_id,
                    "content_type_id": content_type_id,
                    "object_id": object_id,
                    "notification_type": notification_type,
                    "event_type": "notification_content_type_not_found",
                },
            )
            return


@app.task(base=QueueOnce, once={"keys": ["user_id"], "graceful": True})
def send_channel_notify_event(user_id, update_list=True):
    """
    Асинхронная Celery задача для отправки обновления счетчика непрочитанных уведомлений
    через Channels WebSocket пользователю.
    """
    unread_notifications_count = Notification.objects.filter(user_id=user_id, is_read=False).count()

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user_id}",
        {
            "type": "notify",
            "unread_notifications_count": unread_notifications_count,
            "update_list": update_list,
        },
    )
