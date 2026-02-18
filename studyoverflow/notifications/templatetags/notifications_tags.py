from typing import TYPE_CHECKING

from django import template
from notifications.models import Notification


if TYPE_CHECKING:
    from users.models import User as UserType


register = template.Library()


@register.simple_tag
def get_unread_notifications_count(user: "UserType"):
    """
    Simple_tag, возвращающий количество непрочитанных уведомлений для конкретного пользователя.
    """
    if not user.is_authenticated:
        return 0
    return Notification.objects.filter(user=user, is_read=False).count()
