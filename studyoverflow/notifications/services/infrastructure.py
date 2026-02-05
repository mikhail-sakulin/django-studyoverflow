from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils.text import Truncator
from notifications.models import NotificationType
from notifications.tasks import create_notification, send_channel_notify_event
from posts.models import Comment, Like, Post


User = get_user_model()


def handle_send_channel_notify_event(notification):
    transaction.on_commit(
        lambda: send_channel_notify_event.apply_async(
            kwargs={"user_id": notification.user_id},
        )
    )


def handle_notification_post_like(like: Like):
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
            content_type_id=ContentType.objects.get_for_model(Like).id,
            object_id=like.id,
        )
    )


def handle_notification_comment_like(like: Like):
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
            content_type_id=ContentType.objects.get_for_model(Like).id,
            object_id=like.id,
        )
    )


def handle_notification_post_created(post: Post):
    message = f'Вы опубликовали новый пост "{Truncator(post.title).chars(15)}".'

    transaction.on_commit(
        lambda: create_notification.delay(
            user_id=post.author_id,
            actor_id=post.author_id,
            message=message,
            notification_type=NotificationType.POST,
            content_type_id=ContentType.objects.get_for_model(Post).id,
            object_id=post.id,
        )
    )


def handle_notification_comment_on_post_created(comment: Comment):
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
            content_type_id=ContentType.objects.get_for_model(Comment).id,
            object_id=comment.id,
        )
    )


def handle_notification_reply_to_comment_created(comment: Comment):
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
            content_type_id=ContentType.objects.get_for_model(Comment).id,
            object_id=comment.id,
        )
    )


def handle_notification_user_created(user: AbstractUser):
    message = "Вы успешно зарегистрировались!"

    transaction.on_commit(
        lambda: create_notification.delay(
            user_id=user.pk,
            actor_id=user.pk,
            message=message,
            notification_type=NotificationType.REGISTER,
            content_type_id=ContentType.objects.get_for_model(User).id,
            object_id=user.pk,
        )
    )
