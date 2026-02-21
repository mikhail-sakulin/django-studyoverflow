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
