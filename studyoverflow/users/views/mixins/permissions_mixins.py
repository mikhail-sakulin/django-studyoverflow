from typing import Optional

from django.core.exceptions import PermissionDenied
from django.http import HttpRequest
from users.services import is_author_or_moderator


class IsAuthorOrModeratorMixin:
    """
    Mixin для проверки прав на изменение объекта.

    Доступ разрешён, если выполняется одно из условий:
    - Пользователь является автором объекта
    - Пользователь имеет permission на модерацию объекта
    """

    permission_required: Optional[str] = None
    request: HttpRequest

    def has_permission(self, obj):
        return is_author_or_moderator(
            user=self.request.user, obj=obj, permission_required=self.permission_required
        )

    def dispatch(self, request, *args, **kwargs):
        """
        Проверяет права пользователя перед выполнением действия.
        """
        obj = self.get_object()  # type: ignore[attr-defined]

        if not self.has_permission(obj):
            raise PermissionDenied("Недостаточно прав для выполнения этого действия.")

        return super().dispatch(request, *args, **kwargs)  # type: ignore[misc]


class SocialUserPasswordChangeForbiddenMixin:
    """
    Миксин, запрещающий смену пароля для пользователей с авторизацией через соцсеть.
    """

    def dispatch(self, request, *args, **kwargs):
        """
        Проверяет возможность смены пароля.
        """
        if request.user.is_authenticated and getattr(request.user, "is_social", False):
            raise PermissionDenied(
                "Сменить пароль невозможно при авторизации через социальную сеть."
            )

        return super().dispatch(request, *args, **kwargs)  # type: ignore[misc]
