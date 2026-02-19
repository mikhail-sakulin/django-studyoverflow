from typing import Optional

from django.core.exceptions import PermissionDenied
from django.http import HttpRequest


class IsAuthorOrModeratorMixin:
    """
    Mixin для проверки прав на изменение объекта.

    Доступ разрешён, если выполняется одно из условий:
    - Пользователь является автором объекта (obj.author_id == user.pk или obj.user_id == user.pk)
    - Пользователь имеет permission на модерацию объекта
    """

    permission_required: Optional[str] = None
    request: HttpRequest

    def has_permission(self, obj):
        user = self.request.user

        if not user.is_authenticated:
            return False

        if hasattr(obj, "author") and obj.author_id == user.pk:
            return True

        if hasattr(obj, "user") and obj.user_id == user.pk:
            return True

        if self.permission_required and user.has_perm(self.permission_required):
            return True

        return False

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
