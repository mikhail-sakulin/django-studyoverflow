from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model


if TYPE_CHECKING:
    from users.models import User


def can_moderate(actor: "User", target: "User") -> bool:
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
