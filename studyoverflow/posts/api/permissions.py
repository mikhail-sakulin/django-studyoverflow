from rest_framework import permissions
from users.services import is_author_or_moderator


class IsAuthorOrModeratorPermission(permissions.BasePermission):
    """
    Класс-permission для проверки прав на изменение объекта.

    Доступ разрешён, если выполняется одно из условий:
    - Пользователь является автором объекта
    - Пользователь имеет permission на модерацию объекта
    """

    def __init__(self, moderate_permission):
        self.moderate_permission = moderate_permission

    def has_object_permission(self, request, view, obj):
        return is_author_or_moderator(
            user=request.user, obj=obj, permission_required=self.moderate_permission
        )
