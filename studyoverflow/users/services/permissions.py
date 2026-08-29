from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model


if TYPE_CHECKING:
    from users.models import User


def can_moderate(actor: User, target: User) -> bool:
    """
    Проверяет, может ли пользователь actor модерировать пользователя target.

    Бросает PermissionDenied, если модерировать нельзя.
    """
    user_model = get_user_model()

    role_priority = {
        user_model.Role.ADMIN: 3,
        user_model.Role.MODERATOR: 2,
        user_model.Role.STAFF_VIEWER: -1,
        user_model.Role.USER: -1,
    }

    if actor == target:
        return False

    if role_priority[actor.role] <= role_priority[target.role]:
        return False

    return True


def is_author_or_moderator(user, obj, permission_required: str | None = None) -> bool:
    """
    Проверяет права на изменение объекта.

    Доступ разрешён, если выполняется одно из условий:
    - Пользователь является автором объекта (obj.author_id == user.pk или obj.user_id == user.pk)
    - Пользователь имеет permission на модерацию объекта
    """
    if not user.is_authenticated:
        return False

    # Проверка авторства
    is_author = (hasattr(obj, "author_id") and obj.author_id == user.pk) or (
        hasattr(obj, "user_id") and obj.user_id == user.pk
    )
    if is_author:
        return True

    # Проверка прав модератора
    if permission_required and user.has_perm(permission_required):
        return True

    return False


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
