"""
Обработчики для создания уведомлений.

Содержатся функции-хендлеры, которые формируют сообщения и запускают
асинхронные задачи (Celery) для создания уведомлений для различных событий.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils.text import Truncator
from notifications.models import Notification, NotificationType
from notifications.tasks import create_notification, send_channel_notify_event
from posts.models import Comment, Like, Post


if TYPE_CHECKING:
    from users.models import User


def handle_send_channel_notify_event(notification: Notification) -> None:
    """
    Обработчик для отправки обновления счетчика непрочитанных уведомлений через Channels WebSocket.

    Запускает асинхронную Celery задачу для отправки обновления счетчика непрочитанных уведомлений
    через Channels WebSocket пользователю после фиксации транзакции.
    """
    transaction.on_commit(
        lambda: send_channel_notify_event.apply_async(
            kwargs={"user_id": notification.user_id},
        )
    )


def handle_notification_post_like(like: Like) -> None:
    """
    Обработчик для уведомления о лайке поста.

    Формирует сообщение о лайке поста и запускает асинхронную Celery задачу
    для создания уведомления Notification после фиксации транзакции.
    """
    post = like.content_object

    if post.author_id == like.user_id:
        message = f'Вы лайкнули свой пост "{Truncator(post.title).chars(15)}".'
    else:
        message = (
            f"Пользователь {like.user.username} "
            f'лайкнул ваш пост "{Truncator(post.title).chars(15)}".'
        )

    transaction.on_commit(
        lambda: create_notification.delay(
            user_id=post.author_id,
            actor_id=like.user_id,
            message=message,
            notification_type=NotificationType.LIKE_POST,
            content_type_id=ContentType.objects.get_for_model(Like).pk,
            object_id=like.pk,
        )
    )


def handle_notification_comment_like(like: Like) -> None:
    """
    Обработчик для уведомления о лайке комментария через Channels WebSocket.

    Формирует сообщение о лайке комментария и запускает асинхронную Celery задачу
    для создания уведомления Notification после фиксации транзакции.
    """
    comment = like.content_object

    if comment.author_id == like.user_id:
        message = f'Вы лайкнули свой комментарий "{Truncator(comment.content).chars(15)}".'
    else:
        message = (
            f"Пользователь {like.user.username} "
            f'лайкнул ваш комментарий "{Truncator(comment.content).chars(15)}".'
        )

    transaction.on_commit(
        lambda: create_notification.delay(
            user_id=comment.author_id,
            actor_id=like.user_id,
            message=message,
            notification_type=NotificationType.LIKE_COMMENT,
            content_type_id=ContentType.objects.get_for_model(Like).pk,
            object_id=like.pk,
        )
    )


def handle_notification_post_created(post: Post) -> None:
    """
    Обработчик для уведомления о создании нового поста.

    Формирует сообщение о публикации нового поста и запускает асинхронную Celery задачу
    для создания уведомления Notification после фиксации транзакции.
    """
    message = f'Вы опубликовали новый пост "{Truncator(post.title).chars(15)}".'

    transaction.on_commit(
        lambda: create_notification.delay(
            user_id=post.author_id,
            actor_id=post.author_id,
            message=message,
            notification_type=NotificationType.POST,
            content_type_id=ContentType.objects.get_for_model(Post).pk,
            object_id=post.pk,
        )
    )


def handle_notification_comment_on_post_created(comment: Comment) -> None:
    """
    Обработчик для уведомления о новом комментарии к посту.

    Формирует сообщение о новом комментарии к посту и запускает асинхронную Celery задачу
    для создания уведомления Notification после фиксации транзакции.
    """
    if comment.author_id == comment.post.author_id:
        message = (
            f"Вы оставили комментарий "
            f'"{Truncator(comment.content).chars(15)}" '
            f'к вашему посту "{Truncator(comment.post.title).chars(15)}".'
        )
    else:
        message = (
            f"Пользователь {comment.author.username} оставил комментарий "
            f'"{Truncator(comment.content).chars(15)}" '
            f'к вашему посту "{Truncator(comment.post.title).chars(15)}".'
        )

    transaction.on_commit(
        lambda: create_notification.delay(
            user_id=comment.post.author_id,
            actor_id=comment.author_id,
            message=message,
            notification_type=NotificationType.COMMENT,
            content_type_id=ContentType.objects.get_for_model(Comment).pk,
            object_id=comment.pk,
        )
    )


def handle_notification_reply_to_comment_created(comment: Comment) -> None:
    """
    Обработчик для уведомления о новом ответе на комментарий.

    Формирует сообщение о новом ответе на комментарий и запускает асинхронную Celery задачу
    для создания уведомления Notification после фиксации транзакции.
    """
    if comment.author_id == comment.reply_to.author_id:
        message = (
            f"Вы ответили "
            f'"{Truncator(comment.content).chars(15)}" '
            f'на ваш комментарий "{Truncator(comment.reply_to.content).chars(15)}".'
        )
    else:
        message = (
            f"Пользователь {comment.author.username} ответил "
            f'"{Truncator(comment.content).chars(15)}" '
            f'на ваш комментарий "{Truncator(comment.reply_to.content).chars(15)}".'
        )

    transaction.on_commit(
        lambda: create_notification.delay(
            user_id=comment.reply_to.author_id,
            actor_id=comment.author_id,
            message=message,
            notification_type=NotificationType.REPLY,
            content_type_id=ContentType.objects.get_for_model(Comment).pk,
            object_id=comment.pk,
        )
    )


def handle_notification_user_created(user: User) -> None:
    """
    Обработчик для уведомления о регистрации пользователя.

    Формирует сообщение о регистрации нового пользователя и запускает асинхронную Celery задачу
    для создания уведомления Notification после фиксации транзакции.
    """
    message = "Вы успешно зарегистрировались!"

    user_model = get_user_model()

    transaction.on_commit(
        lambda: create_notification.delay(
            user_id=user.pk,
            actor_id=user.pk,
            message=message,
            notification_type=NotificationType.REGISTER,
            content_type_id=ContentType.objects.get_for_model(user_model).pk,
            object_id=user.pk,
        )
    )
