from django import template
from notifications.models import Notification


register = template.Library()


@register.simple_tag
def get_unread_notifications_count(user):
    """
    Simple_tag, возвращающий количество непрочитанных уведомлений для конкретного пользователя.
    """
    if not user.is_authenticated:
        return 0
    return Notification.objects.filter(user=user, is_read=False).count()
