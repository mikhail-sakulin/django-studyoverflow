from typing import Any, Optional

from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.http import HttpRequest

from users.services.permissions import is_author_or_moderator


class IsAuthorOrModeratorMixin:
    """
    Mixin для проверки прав на изменение объекта.

    Доступ разрешён, если выполняется одно из условий:
    - Пользователь является автором объекта
    - Пользователь имеет permission на модерацию объекта

    При использовании во views данный миксин должен указываться после LoginRequiredMixin,
    тогда анонимные пользователи получат редирект на логин, а не 403.
    """

    moderator_permission_name: Optional[str] = None
    request: HttpRequest

    def can_modify_object(self, obj):
        return is_author_or_moderator(
            user=self.request.user, obj=obj, permission_required=self.moderator_permission_name
        )

    def get_object(self, queryset: Optional[QuerySet] = None) -> Any:
        """
        Проверяет права пользователя перед выполнением действия.
        """
        obj = super().get_object(queryset)  # type: ignore[misc]

        if not self.can_modify_object(obj):
            raise PermissionDenied("Недостаточно прав для выполнения этого действия.")

        return obj


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
