from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.core.exceptions import PermissionDenied
from django.utils import timezone

from .permissions import can_moderate


if TYPE_CHECKING:
    from users.models import User


logger = logging.getLogger(__name__)


def block_user_service(
    moderator: User, target_user: User, source: str = "unknown"
) -> tuple[bool, str]:
    """Блокирует пользователя, используя сервисную функцию."""
    return _set_user_block_state(moderator, target_user, is_blocked=True, source=source)


def unblock_user_service(
    moderator: User, target_user: User, source: str = "unknown"
) -> tuple[bool, str]:
    """Разблокирует пользователя, используя сервисную функцию."""
    return _set_user_block_state(moderator, target_user, is_blocked=False, source=source)


def _set_user_block_state(
    moderator: User, target_user: User, is_blocked: bool, source: str = "unknown"
) -> tuple[bool, str]:
    """
    Блокирует или разблокирует пользователя.

    Внутренняя сервисная функция для управления статусом блокировки пользователя.
    """
    if not can_moderate(moderator, target_user):
        raise PermissionDenied(
            "Нельзя модерировать пользователя с равной или более высокой ролью. / "
            "Нельзя модерировать самого себя."
        )

    if target_user.is_blocked == is_blocked:
        state = "заблокирован" if is_blocked else "разблокирован"
        return False, f"Пользователь {target_user.username} уже {state}."

    target_user.is_blocked = is_blocked
    target_user.blocked_at = timezone.now() if is_blocked else None
    target_user.blocked_by = moderator if is_blocked else None
    target_user.save(update_fields=["is_blocked", "blocked_at", "blocked_by"])

    action_for_log = "заблокировал" if is_blocked else "разблокировал"
    action_for_message = "заблокирован" if is_blocked else "разблокирован"

    # Логирование
    logger.info(
        f"Модератор {moderator.username} {action_for_log} пользователя {target_user.username}.",
        extra={
            "moderator_id": moderator.pk,
            "target_user_id": target_user.pk,
            "event_type": f"user_{'blocked' if is_blocked else 'unblocked'}",
            "source": source,  # источник запроса (web / api)
        },
    )

    return True, f"Пользователь {target_user.username} успешно {action_for_message}."


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
