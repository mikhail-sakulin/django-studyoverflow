from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import ListView, TemplateView

from notifications.mixins import NotificationOptimizeMixin
from notifications.models import Notification
from notifications.signals import notification_delete_reason
from notifications.tasks import send_channel_notify_event
from posts.mixins import LoginRequiredRedirectHTMXMixin


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
            return HttpResponseForbidden("Not allowed")  # 403

        # Устанавливается переменная контекста для текущего запроса.
        # Она используется обработчиком сигнала post_delete как флаг, что инициатором
        # удаления уведомления был сам пользователь и что обновлять список уведомлений не нужно.
        token = notification_delete_reason.set("self_delete")
        try:
            notification.delete()
        finally:
            # Сброс переменной контекста на исходное значение (None).
            notification_delete_reason.reset(token)

        return HttpResponse()


class NotificationDeleteAllView(LoginRequiredRedirectHTMXMixin, View):
    """
    Удаляет все уведомления текущего пользователя.
    """

    def post(self, request, *args, **kwargs):
        notifications = Notification.objects.filter(user=request.user)

        # 1) Перед bulk-операцией удаления всех уведомлений пользователя стоит отключать выполнение
        # обработчика сигнала post_delete, чтобы каждому python-объекту уведомления не пришлось
        # присваивать флаг (сам пользователь удаляет уведомление, или нет) и чтобы celery-задача
        # обновления числа уведомлений у клиента не вызывалась множество раз подряд.
        #
        # 2) Но, поскольку post_delete - это глобальный синглтон на весь python-процесс, то в
        # многопоточном или асинхронном режимах (в проекте используется Daphne) использовать
        # post_delete.disconnect(notification_count_when_notification_deleted, sender=Notification)
        # нельзя, так как тогда обработчик отключится от сигнала для всех потоков процесса,
        # отключать обработчик сигнала от сигнала можно только в синхронном режиме в одном потоке.
        #
        # 3) Вместо post_delete.disconnect(...) используется contextvars.ContextVar. Для каждого
        # запроса создаётся свой contextvars.copy_context(), который выполняется в своём потоке
        # из thread pool. Значения ContextVar, установленные внутри одного запроса, не видны и
        # не влияют на конкурентно выполняющийся другой запрос. Это решает проблему
        # post_delete.disconnect(...), а также позволяет не использовать флаг
        # _self_initiated_delete для каждого python-объекта уведомления.
        #
        # 4) Celery-задача send_channel_notify_event для обновления числа уведомлений не будет
        # вызываться многократно, потому что она защищена QueueOnce с keys=["user_id"] - пока
        # одна задача выполняется, ее дубликат не будет добавлен в очередь касательного
        # одного пользователя.
        #
        # Устанавливается переменная контекста для текущего запроса.
        # Она используется обработчиком сигнала post_delete как флаг, что инициатором
        # удаления уведомлений был сам пользователь и что обновлять список уведомлений не нужно.
        token = notification_delete_reason.set("self_delete")
        try:
            notifications.delete()
        finally:
            # Сброс переменной контекста на исходное значение (None).
            notification_delete_reason.reset(token)

        return HttpResponse()
