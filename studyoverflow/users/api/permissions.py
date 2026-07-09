from rest_framework import permissions


class CanBlockUserPermission(permissions.BasePermission):
    """
    Проверяет наличие у пользователя права на блокировку другого пользователя (модерацию).
    """

    def has_permission(self, request, view):
        return request.user.has_perm("users.block_user")


class UserPasswordNotSocialPermission(permissions.BasePermission):
    """
    Проверяет, что пользователь зарегистрировался не через соцсеть.
    """

    message = "Пользователи, зарегистрированные через социальные сети, не могут изменять пароль."

    def has_permission(self, request, view):
        return not getattr(request.user, "is_social", False)
