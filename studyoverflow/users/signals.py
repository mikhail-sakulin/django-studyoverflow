import logging

from allauth.account.signals import user_signed_up
from django.contrib.auth import get_user_model, user_logged_in, user_logged_out, user_login_failed
from django.contrib.auth.models import Group, Permission
from django.db import transaction
from django.db.models import Q
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from users.services import delete_cache_user, get_user_avatar_paths_list, remove_user_offline
from users.tasks import delete_files_from_storage_task


UserModel = get_user_model()

logger = logging.getLogger(__name__)


# Пары (app_label, codename) прав, которые будет иметь группа "Moderators"
MODERATOR_PERMISSIONS = [
    # posts.Comment
    ("posts", "add_comment"),
    ("posts", "change_comment"),
    ("posts", "delete_comment"),
    ("posts", "moderate_comment"),
    # posts.Post
    ("posts", "add_post"),
    ("posts", "change_post"),
    ("posts", "delete_post"),
    ("posts", "moderate_post"),
    # users.User
    ("users", "block_user"),
]

# Пары (app_label, codename) прав, которые получит группа "StaffViewers"
STAFF_PERMISSIONS = [
    ("account", "view_emailaddress"),
    ("account", "view_emailconfirmation"),
    ("admin", "view_logentry"),
    ("auth", "view_group"),
    ("auth", "view_permission"),
    ("contenttypes", "view_contenttype"),
    ("notifications", "view_notification"),
    ("posts", "view_comment"),
    ("posts", "view_like"),
    ("posts", "view_tag"),
    ("posts", "view_post"),
    ("posts", "view_posttag"),
    ("sessions", "view_session"),
    ("sites", "view_site"),
    ("socialaccount", "view_socialaccount"),
    ("socialaccount", "view_socialapp"),
    ("socialaccount", "view_socialtoken"),
    ("users", "view_user"),
]


def _perms_queryset(pairs):
    """
    Строит queryset Permission, точно соответствующих списку пар (app_label, codename).
    """
    q = Q()
    for app_label, codename in pairs:
        q |= Q(content_type__app_label=app_label, codename=codename)
    return Permission.objects.filter(q)


def sync_default_groups(sender, **kwargs):
    """
    Обработчик post_migrate: создаёт/обновляет группы Moderators и StaffViewers с нужными правами.
    """
    moderator_group, _ = Group.objects.get_or_create(name="Moderators")
    staff_group, _ = Group.objects.get_or_create(name="StaffViewers")

    moderator_group.permissions.set(_perms_queryset(MODERATOR_PERMISSIONS))
    staff_group.permissions.set(_perms_queryset(STAFF_PERMISSIONS))


@receiver(post_delete, sender=UserModel)
def delete_user_avatars_after_user_deleted(sender, instance, **kwargs):
    """
    Сигнал, срабатывающий после удаления пользователя.

    Удаляет файлы аватаров пользователя из хранилища после удаления аккаунта.

    Использует transaction.on_commit, чтобы файлы удалялись только после
    успешного завершения транзакции БД.
    """
    paths_to_delete = get_user_avatar_paths_list(instance)

    if paths_to_delete:
        transaction.on_commit(lambda: delete_files_from_storage_task.delay(paths_to_delete))


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """
    Сигнал, срабатывающий при успешной авторизации пользователя.

    Логирует факт входа в систему с записью данных пользователя.
    """
    source = getattr(request, "source_for_logging", "unknown") if request else "unknown"

    logger.info(
        f"Пользователь авторизовался: {user.username}.",
        extra={
            "username": user.username,
            "user_id": user.pk,
            "email": user.email,
            "is_social": user.is_social,
            "event_type": "user_login",
            "source": source,
        },
    )


@receiver(user_signed_up)
def log_user_signup(sender, request, user, **kwargs):
    """
    Сигнал (из allauth), срабатывающий при регистрации нового пользователя.

    При регистрации через соцсети срабатывает автоматически, при регистрации по
    логину и паролю требует ручного вызова.

    Логирует создание аккаунта и фиксирует социальный провайдер,
    если регистрация прошла через соцсеть.
    """
    sociallogin = kwargs.get("sociallogin")

    provider = sociallogin.account.provider if sociallogin else None

    source = getattr(request, "source_for_logging", "unknown") if request else "unknown"

    logger.info(
        f"Новый пользователь зарегистрировался: {user.username}.",
        extra={
            "username": user.username,
            "user_id": user.pk,
            "email": user.email,
            "is_social": user.is_social,
            "provider": provider,
            "event_type": "user_registration",
            "source": source,
        },
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """
    Сигнал, срабатывающий при выходе пользователя из системы.

    Логирует выход пользователя из системы с сохранением данных пользователя.
    """
    source = getattr(request, "source_for_logging", "unknown") if request else "unknown"

    logger.info(
        f"Пользователь вышел из системы: {user.username}.",
        extra={
            "username": user.username,
            "user_id": user.pk,
            "email": user.email,
            "is_social": user.is_social,
            "event_type": "user_logout",
            "source": source,
        },
    )


@receiver(user_logged_out)
def remove_user_offline_when_logged_out(sender, request, user, **kwargs):
    """
    Сигнал, срабатывающий при выходе пользователя из системы.

    Удаляет информацию о присутствии пользователя (online status) из Redis.
    """
    remove_user_offline(user.pk)


@receiver(post_delete, sender=UserModel)
def log_user_deletion(sender, instance, **kwargs):
    """
    Сигнал, срабатывающий после удаления пользователя.

    Логирует удаление записи аккаунта из БД.
    """
    user = instance
    logger.info(
        f"Аккаунт удален: {user.username}.",
        extra={
            "username": user.username,
            "user_id": user.pk,
            "email": user.email,
            "is_social": user.is_social,
            "event_type": "user_deletion",
        },
    )


# Если authenticate(...) не может аутентифицировать пользователя и возвращает не пользователя,
# а None, то срабатывает сигнал user_login_failed.
@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    """
    Сигнал, срабатывающий при неудачной попытке входа.

    Логирует попытку авторизации с указанием введенного логина
    для мониторинга.
    """
    login_attempted = credentials.get("username") or credentials.get("email") or "unknown"

    source = getattr(request, "source_for_logging", "unknown") if request else "unknown"

    logger.info(
        f"Неудачная попытка входа для пользователя: {login_attempted}.",
        extra={
            "attempted_login": login_attempted,
            "event_type": "auth_failed",
            "source": source,
        },
    )


@receiver(post_save, sender=UserModel)
def invalidate_user_object_cache_on_save(sender, instance, created, update_fields, **kwargs):
    """
    Удаляет кэш объекта пользователя при изменении данных пользователя, кроме пароля.
    """
    if created:
        return

    if update_fields and "password" in update_fields:
        return

    delete_cache_user(instance.username)


@receiver(post_delete, sender=UserModel)
def invalidate_user_object_cache_on_delete(sender, instance, **kwargs):
    """
    Удаляет кэш объекта пользователя при его удалении.
    """
    delete_cache_user(instance.username)
