from django import template
from users.services.infrastructure import is_user_online


register = template.Library()


@register.simple_tag
def online_status_tag(user):
    if not user.is_authenticated:
        return None

    if is_user_online(user.id):
        return True

    return user.last_seen
