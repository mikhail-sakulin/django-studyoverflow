import logging

from asgiref.sync import async_to_sync
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from celery_once import QueueOnce
from channels.layers import get_channel_layer
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from notifications.models import Notification


logger = logging.getLogger(__name__)


@shared_task(
    ignore_result=True,
    acks_late=True,
    reject_on_worker_lost=True,
    soft_time_limit=20,
    time_limit=30,
)
def create_notification(
    user_id: int,
    actor_id: int,
    message: str,
    notification_type: str,
    content_type_id: int,
    object_id: int,
) -> None:
    """
    Celery задача для создания уведомления Notification.
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


# Используется библиотека celery_once, чтобы предотвратить запуск дубликатов одной и той же
# задачи (параметры, переданные в задачу, учитываются тоже).
# Когда задача с классом QueueOnce вызывается (.delay() или .apply_async()), она не отправляется
# сразу в очередь брокера, она создает ключ-замок lock в Redis для задачи с учетом
# переданных параметров. Замок удаляется, когда задача завершает выполнение в воркере.
@shared_task(  # type: ignore
    # Указывается класс самой задачи, по умолчанию base=celery.Task, в QueueOnce переопределены
    # методы отправки в очередь, чтобы задачи сначала проверяли наличие блокировки в Redis.
    base=QueueOnce,
    # Без ключей блокировки блокировка работала бы на имя функции.
    # keys": ["user_id"] делает блокировку уникальной для конкретных аргументов.
    # graceful=True - игнорирование при запуске дубликата задачи, при graceful=False
    # Celery выбрасывает исключение в коде, где вызывается дубликат,
    # с True исключение не вызывается.
    once={"keys": ["user_id"], "graceful": True},
    ignore_result=True,
    acks_late=True,
    reject_on_worker_lost=True,
    autoretry_for=(ConnectionError, SoftTimeLimitExceeded),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
    soft_time_limit=15,
    time_limit=25,
)
def send_channel_notify_event(user_id: int, update_list=True) -> None:
    """
    Celery задача для отправки обновления счетчика непрочитанных уведомлений
    через Channels WebSocket пользователю.
    """
    unread_notifications_count = Notification.objects.filter(user_id=user_id, is_read=False).count()

    channel_layer = get_channel_layer()

    # Внутри async def можно было бы написать await channel_layer.group_send(...) - для await
    # возвращается корутина.
    #
    # Внутри синхронной def нужно оборачивать корутину в async_to_sync.
    async_to_sync(channel_layer.group_send)(
        f"user_{user_id}",
        {
            "type": "notify",
            "unread_notifications_count": unread_notifications_count,
            "update_list": update_list,
        },
    )
