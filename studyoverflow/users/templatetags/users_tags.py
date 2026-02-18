from typing import TYPE_CHECKING

from django import template
from django.contrib.auth import get_user_model
from users.services import can_moderate, is_user_online


register = template.Library()

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser

UserModel = get_user_model()

role_mapping = {
    UserModel.Role.ADMIN: ("role-admin", "Admin"),
    UserModel.Role.MODERATOR: ("role-moderator", "Moderator"),
    UserModel.Role.STAFF_VIEWER: ("role-staff", "Staff"),
}


@register.simple_tag
def online_status_tag(user):
    """
    Simple_tag, возвращает статус активности пользователя.

    Если пользователь онлайн, возвращает True.
    Если пользователь не онлайн, возвращает дату последнего визита (last_seen).
    Если пользователь не аутентифицирован, возвращает None.
    """
    if not user.is_authenticated:
        return None

    if is_user_online(user.id):
        return True

    return user.last_seen


@register.inclusion_tag("users/_role_badge.html")
def user_role_badge(user):
    """
    Возвращает контекст для отображения бейджика роли пользователя.

    Словарь контекста содержит:
    - css_role_badge_class: CSS-класс для отображения цвета/стиля;
    - badge: название роли для вывода в шаблоне.

    Если роль пользователя не определена, возвращает None для обоих полей.
    """
    css_role_badge_class, badge = role_mapping.get(user.role, (None, None))

    return {
        "css_role_badge_class": css_role_badge_class,
        "badge": badge,
    }


@register.simple_tag
def can_actor_moderate_target(actor: "AbstractUser", target: "AbstractUser") -> bool:
    """
    Проверяет, может ли один пользователь (actor) модерировать другого (target).

    Возвращает:
    - True, если actor аутентифицирован и имеет права модерирования target;
    - False в противном случае.
    """
    if not actor.is_authenticated or not target:
        return False

    return can_moderate(actor, target)
