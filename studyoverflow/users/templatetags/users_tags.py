from django import template
from django.contrib.auth import get_user_model
from users.services.infrastructure import is_user_online


register = template.Library()

User = get_user_model()  # noqa: N806

role_mapping = {
    User.Role.ADMIN: ("role-admin", "Admin"),
    User.Role.MODERATOR: ("role-moderator", "Moderator"),
    User.Role.STAFF_VIEWER: ("role-staff", "Staff"),
}


@register.simple_tag
def online_status_tag(user):
    if not user.is_authenticated:
        return None

    if is_user_online(user.id):
        return True

    return user.last_seen


@register.inclusion_tag("users/_role_badge.html")
def user_role_badge(user):
    css_role_badge_class, badge = role_mapping.get(user.role, (None, None))

    return {
        "css_role_badge_class": css_role_badge_class,
        "badge": badge,
    }
