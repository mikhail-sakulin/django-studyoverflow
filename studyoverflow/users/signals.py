import logging

from allauth.account.signals import user_signed_up
from django.contrib.auth import get_user_model, user_logged_in, user_logged_out, user_login_failed
from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver
from users.services.infrastructure import get_user_avatar_paths_list, remove_user_offline
from users.tasks import delete_files_from_storage_task


User = get_user_model()

logger = logging.getLogger(__name__)


@receiver(post_delete, sender=User)
def notification_count_when_notification_deleted(sender, instance, **kwargs):
    paths_to_delete = get_user_avatar_paths_list(instance)

    if paths_to_delete:
        transaction.on_commit(lambda: delete_files_from_storage_task.delay(paths_to_delete))


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    logger.info(
        f"Пользователь авторизовался: {user.username}.",
        extra={
            "username": user.username,
            "user_id": user.id,
            "email": user.email,
            "is_social": user.is_social,
            "event_type": "user_login",
        },
    )


@receiver(user_signed_up)
def log_user_signup(sender, request, user, **kwargs):
    sociallogin = kwargs.get("sociallogin")

    provider = sociallogin.account.provider if sociallogin else None

    logger.info(
        f"Новый пользователь зарегистрировался: {user.username}.",
        extra={
            "username": user.username,
            "user_id": user.id,
            "email": user.email,
            "is_social": user.is_social,
            "provider": provider,
            "event_type": "user_registration",
        },
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    logger.info(
        f"Пользователь вышел из системы: {user.username}.",
        extra={
            "username": user.username,
            "user_id": user.id,
            "email": user.email,
            "is_social": user.is_social,
            "event_type": "user_logout",
        },
    )


@receiver(user_logged_out)
def remove_user_offline_when_logged_out(sender, request, user, **kwargs):
    remove_user_offline(user.id)


@receiver(post_delete, sender=User)
def log_user_deletion(sender, instance, **kwargs):
    user = instance
    logger.info(
        f"Аккаунт удален: {user.username}.",
        extra={
            "username": user.username,
            "user_id": user.id,
            "email": user.email,
            "is_social": user.is_social,
            "event_type": "user_deletion",
        },
    )


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    login_attempted = credentials.get("username") or credentials.get("email") or "unknown"

    logger.info(
        f"Неудачная попытка входа для пользователя: {login_attempted}.",
        extra={
            "attempted_login": login_attempted,
            "event_type": "auth_failed",
        },
    )
