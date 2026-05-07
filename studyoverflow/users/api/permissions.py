from rest_framework import permissions


class CanBlockUserPermission(permissions.BasePermission):
    """
    Проверяет наличие у пользователя права на блокировку другого пользователя (модерацию).
    """

    def has_permission(self, request, view):
        return request.user.has_perm("users.block_user")
