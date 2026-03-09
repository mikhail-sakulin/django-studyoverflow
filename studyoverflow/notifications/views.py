from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import ListView, TemplateView
from notifications.mixins import NotificationOptimizeMixin
from notifications.models import Notification
from notifications.tasks import send_channel_notify_event
from posts.views.mixins import LoginRequiredRedirectHTMXMixin


class NotificationTemplateView(LoginRequiredMixin, TemplateView):
    """Отображает базовый шаблон страницы уведомлений."""

    template_name = "notifications/notification_base.html"


class NotificationListView(LoginRequiredRedirectHTMXMixin, NotificationOptimizeMixin, ListView):
    """
    Возвращает список уведомлений текущего пользователя.
    """

    model = Notification
    template_name = "notifications/_notification_list.html"
    context_object_name = "notification_list"

    def get_queryset(self):
        queryset = super().get_queryset()

        queryset = queryset.filter(user=self.request.user)

        queryset = self.optimize_notification_queryset(queryset)

        return queryset


class NotificationMarkReadView(LoginRequiredRedirectHTMXMixin, View):
    """
    Помечает уведомление как прочитанное, если оно принадлежит текущему пользователю.
    """

    def post(self, request, *args, **kwargs):
        notification = get_object_or_404(Notification, pk=kwargs["pk"])

        if notification.user != request.user:
            return HttpResponseForbidden("Not allowed")

        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=["is_read"])

        return HttpResponse()


class NotificationMarkAllReadView(LoginRequiredRedirectHTMXMixin, View):
    """
    Помечает все уведомления текущего пользователя прочитанными и создает
    Celery задачу для обновления счетчика непрочитанных уведомлений
    через Channels WebSocket.
    """

    def post(self, request, *args, **kwargs):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)

        send_channel_notify_event.delay(user_id=request.user.pk, update_list=False)

        return HttpResponse()


class NotificationDeleteView(LoginRequiredRedirectHTMXMixin, View):
    """
    Удаляет уведомление текущего пользователя.
    """

    def post(self, request, *args, **kwargs):
        notification = get_object_or_404(Notification, pk=kwargs["pk"])

        if notification.user != request.user:
            return HttpResponseForbidden("Not allowed")

        notification.delete()

        return HttpResponse()


class NotificationDeleteAllView(LoginRequiredRedirectHTMXMixin, View):
    """
    Удаляет все уведомления текущего пользователя.
    """

    def post(self, request, *args, **kwargs):
        notifications = Notification.objects.filter(user=request.user)

        if not notifications.exists():
            return HttpResponse()

        notifications.delete()

        return HttpResponse()
