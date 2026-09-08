import logging
from contextvars import ContextVar

from django.contrib.auth import get_user_model
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from notifications.models import Notification
from notifications.services import (
    handle_notification_comment_like,
    handle_notification_comment_on_post_created,
    handle_notification_post_created,
    handle_notification_post_like,
    handle_notification_reply_to_comment_created,
    handle_notification_user_created,
    handle_send_channel_notify_event,
)
from posts.models import Comment, Like, Post


User = get_user_model()

logger = logging.getLogger(__name__)

# Сохраняет причину удаления уведомления для текущего запроса/контекста выполнения.
# None означает внешнее (каскадное) удаление уведомления из-за удаления связанных
# объектов другими пользователями. Если пользователь удаляет уведомление сам,
# значение должно задаваться "self_delete".
notification_delete_reason: ContextVar[str | None] = ContextVar(
    "notification_delete_reason", default=None
)


@receiver(post_save, sender=Like)
def notification_like_created(sender, instance, created, raw, **kwargs):
    """
    Инициирует создание уведомления при появлении нового лайка на пост или комментарий.

    Не выполняется для "raw" операций (например, при загрузке fixtures).
    """
    if raw:
        return

    if not created:
        return

    if isinstance(instance.content_object, Post):
        handle_notification_post_like(instance)

    elif isinstance(instance.content_object, Comment):
        handle_notification_comment_like(instance)


@receiver(post_save, sender=Post)
def notification_post_created(sender, instance, created, raw, **kwargs):
    """
    Инициирует создание уведомления для автора при успешной публикации поста.

    Не выполняется для "raw" операций (например, при загрузке fixtures).
    """
    if raw:
        return

    if not created:
        return

    handle_notification_post_created(instance)


@receiver(post_save, sender=Comment)
def notification_comment_created(sender, instance, created, raw, **kwargs):
    """
    Инициирует создание уведомлений для автора поста или автора родительского комментария
    при новом комментарии к посту или ответу на комментарий.

    Не выполняется для "raw" операций (например, при загрузке fixtures).
    """
    if raw:
        return

    if not created:
        return

    if instance.reply_to:
        if (
            instance.author_id != instance.post.author_id
            and instance.post.author_id != instance.reply_to.author_id
        ):
            handle_notification_comment_on_post_created(instance)

        handle_notification_reply_to_comment_created(instance)
    else:
        handle_notification_comment_on_post_created(instance)


@receiver(post_save, sender=User)
def notification_user_created(sender, instance, created, raw, **kwargs):
    """
    Инициирует отправку приветственного уведомления новому пользователю после регистрации.

    Не выполняется для "raw" операций (например, при загрузке fixtures).
    """
    if raw:
        return

    if not created:
        return

    handle_notification_user_created(instance)


@receiver(post_save, sender=Notification)
def notification_count_when_notification_created(sender, instance, created, raw, **kwargs):
    """
    Запускает WebSocket-событие для обновления счетчика
    при создании нового уведомления через handler.

    Не выполняется для "raw" операций (например, при загрузке fixtures).
    """
    if raw:
        return

    handle_send_channel_notify_event(instance, update_list=created)


@receiver(post_delete, sender=Notification)
def notification_count_when_notification_deleted(sender, instance, **kwargs):
    """
    Запускает WebSocket-событие для обновления счетчика и списка уведомлений при необходимости
    при удалении уведомления через handler.

    Список уведомлений не обновляется, если уведомление было удалено самим пользователем,
    а не каскадом из-за удаления связанного объекта другим пользователем.
    """
    # Получение значения переменной контекста для текущего запроса для определения, пользователь
    # сам инициировал удаление уведомления, или же нет.
    reason = notification_delete_reason.get()

    if reason == "self_delete":
        handle_send_channel_notify_event(instance, update_list=False, reason="self_delete")
    else:
        handle_send_channel_notify_event(instance, update_list=True, reason="external_delete")


@receiver(post_save, sender=Notification)
def log_notification_created(sender, instance, created, raw, **kwargs):
    """
    Логирует создание уведомления.

    Не выполняется для "raw" операций (например, при загрузке fixtures).
    """
    if raw:
        return

    if not created:
        return

    related_obj_id = instance.object_id if instance.object_id else None
    related_obj_type = str(instance.content_type) if instance.content_type else None

    logger.info(
        f"Создано уведомление: {instance.get_notification_type_display()}",
        extra={
            "for_user": instance.user_id,
            "actor_id": instance.actor_id,
            "notification_type": instance.notification_type,
            "related_object_id": related_obj_id,
            "related_object_type": related_obj_type,
            "event_type": "notification_created",
        },
    )
