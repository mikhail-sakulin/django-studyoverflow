from typing import TYPE_CHECKING, Optional

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest


if TYPE_CHECKING:
    from users.models import User


class IsAuthorOrModeratorMixin:
    """
    Доступ к изменению объекта разрешен, если:
    - пользователь является автором объекта
    - ИЛИ имеет permission на модерацию объекта
    """

    permission_required: Optional[str] = None
    request: HttpRequest

    def has_permission(self, obj):
        user = self.request.user

        if not user.is_authenticated:
            return False

        if hasattr(obj, "author") and obj.author_id == user.id:
            return True

        if hasattr(obj, "user") and obj.user_id == user.id:
            return True

        if self.permission_required and user.has_perm(self.permission_required):
            return True

        return False

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()  # type: ignore[attr-defined]

        if not self.has_permission(obj):
            raise PermissionDenied("Недостаточно прав для выполнения этого действия.")

        return super().dispatch(request, *args, **kwargs)  # type: ignore[misc]


class SocialUserPasswordChangeForbiddenMixin:
    """
    Запрещает смену пароля для пользователей с авторизацией через соцсеть.
    """

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and getattr(request.user, "is_social", False):
            raise PermissionDenied(
                "Сменить пароль невозможно при авторизации через социальную сеть."
            )

        return super().dispatch(request, *args, **kwargs)  # type: ignore[misc]


def can_moderate(actor: "User", target: "User") -> bool:
    """
    Проверяет, может ли actor модерировать target.
    Бросает PermissionDenied, если нельзя.
    """
    UserModel = get_user_model()  # noqa: N806

    role_priority = {
        UserModel.Role.ADMIN: 3,
        UserModel.Role.MODERATOR: 2,
        UserModel.Role.STAFF_VIEWER: -1,
        UserModel.Role.USER: -1,
    }

    if actor == target:
        return False

    if role_priority[actor.role] <= role_priority[target.role]:
        return False

    return True
