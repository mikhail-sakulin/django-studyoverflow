from django.contrib.contenttypes.prefetch import GenericPrefetch
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import ListView, TemplateView
from notifications.models import Notification
from posts.models import Comment, Like, Post

from .tasks import send_channel_notify_event


class NotificationTemplateView(TemplateView):
    template_name = "notifications/notification_base.html"


class NotificationListView(ListView):
    model = Notification
    template_name = "notifications/_notification_list.html"
    context_object_name = "notification_list"

    def get_queryset(self):
        queryset = super().get_queryset()

        queryset = (
            queryset.filter(user=self.request.user)
            .select_related("user", "actor", "content_type")
            .prefetch_related(
                GenericPrefetch(
                    "content_object",
                    [
                        Post.objects.all(),
                        Comment.objects.select_related("post"),
                        Like.objects.prefetch_related(
                            GenericPrefetch(
                                "content_object",
                                [
                                    Post.objects.all(),
                                    Comment.objects.select_related("post"),
                                ],
                            )
                        ),
                    ],
                )
            )
        )

        return queryset


class NotificationMarkReadView(View):
    def post(self, request, *args, **kwargs):
        notification = get_object_or_404(Notification, pk=kwargs["pk"])

        if notification.user != request.user:
            return HttpResponseForbidden("Not allowed")

        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=["is_read"])

        return HttpResponse()


class NotificationMarkAllReadView(View):
    def post(self, request, *args, **kwargs):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)

        send_channel_notify_event.delay(user_id=request.user.id, update_list=False)

        return HttpResponse()


class NotificationDeleteView(View):
    def post(self, request, *args, **kwargs):
        notification = get_object_or_404(Notification, pk=kwargs["pk"])

        if notification.user != request.user:
            return HttpResponseForbidden("Not allowed")

        notification.delete()

        return HttpResponse()


class NotificationDeleteAllView(View):
    def post(self, request, *args, **kwargs):
        notifications = Notification.objects.filter(user=request.user)

        if not notifications.exists():
            return HttpResponse()

        notifications.delete()

        return HttpResponse()
