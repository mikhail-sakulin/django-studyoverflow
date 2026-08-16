import pytest
from django.contrib.contenttypes.models import ContentType

from notifications.models import Notification, NotificationType
from notifications.tasks import create_notification, send_channel_notify_event
from posts.models import Post


@pytest.mark.django_db
class TestCreateNotificationTask:
    def test_create_notification_success(self, user_factory, post_factory):
        """Проверка успешного создания уведомления."""
        user = user_factory()
        actor = user_factory()
        post = post_factory()
        content_type = ContentType.objects.get_for_model(Post)

        create_notification(
            user_id=user.pk,
            actor_id=actor.pk,
            message="Тестовое сообщение",
            notification_type=NotificationType.POST.value,  # type: ignore[attr-defined]
            content_type_id=content_type.pk,
            object_id=post.pk,
        )

        assert Notification.objects.count() == 1

        notification = Notification.objects.first()
        assert notification.user_id == user.pk
        assert notification.actor_id == actor.pk
        assert notification.message == "Тестовое сообщение"
        assert (
            notification.notification_type
            == NotificationType.POST.value  # type: ignore[attr-defined]
        )
        assert notification.content_type == content_type
        assert notification.object_id == post.pk

    def test_create_notification_object_does_not_exist(self, user_factory, mocker):
        """Если целевого объекта (object_id) больше нет в БД, уведомление не создается."""
        mock_notification_create = mocker.patch("notifications.tasks.Notification.objects.create")

        user = user_factory()
        content_type = ContentType.objects.get_for_model(Post)
        non_existent_post_id = 99999

        create_notification(
            user_id=user.pk,
            actor_id=user.pk,
            message="Тестовое сообщение",
            notification_type=NotificationType.POST.value,  # type: ignore[attr-defined]
            content_type_id=content_type.pk,
            object_id=non_existent_post_id,
        )

        mock_notification_create.assert_not_called()

    def test_create_notification_content_type_does_not_exist(self, user_factory, mocker):
        """Если ContentType не найден, логгируется warning и уведомление не создается."""
        mock_logger = mocker.patch("notifications.tasks.logger.warning")
        mock_notification_create = mocker.patch("notifications.tasks.Notification.objects.create")

        user = user_factory()
        invalid_content_type_id = 99999

        create_notification(
            user_id=user.pk,
            actor_id=user.pk,
            message="Тестовое сообщение",
            notification_type=NotificationType.POST.value,  # type: ignore[attr-defined]
            content_type_id=invalid_content_type_id,
            object_id=1,
        )

        mock_notification_create.assert_not_called()

        mock_logger.assert_called_once()
        (log_msg,) = mock_logger.call_args[0]
        assert "не найден" in log_msg
        assert (
            mock_logger.call_args[1]["extra"]["event_type"] == "notification_content_type_not_found"
        )


@pytest.mark.django_db
class TestSendChannelNotifyEventTask:
    def test_send_event_success_counts_only_unread(self, user_factory, post_factory, mocker):
        """
        Проверка подсчета непрочитанных уведомлений
        и отправки данных через channel_layer.
        """
        user = user_factory()

        # Создаются 2 непрочитанных и 1 прочитанное уведомление
        Notification.objects.create(
            user=user,
            actor_id=user.pk,
            notification_type=NotificationType.POST.value,  # type: ignore[attr-defined]
            content_object=post_factory(),
            is_read=False,
        )
        Notification.objects.create(
            user=user,
            actor_id=user.pk,
            notification_type=NotificationType.POST.value,  # type: ignore[attr-defined]
            content_object=post_factory(),
            is_read=False,
        )
        Notification.objects.create(
            user=user,
            actor_id=user.pk,
            notification_type=NotificationType.POST.value,  # type: ignore[attr-defined]
            content_object=post_factory(),
            is_read=True,
        )

        # В celery-задаче
        #
        # channel_layer = get_channel_layer()
        #
        # async_to_sync(channel_layer.group_send)(
        #     group_name,
        #     message
        # )
        mock_get_channel_layer = mocker.patch("notifications.tasks.get_channel_layer")
        mock_channel_layer = mock_get_channel_layer.return_value
        mock_async_to_sync = mocker.patch("notifications.tasks.async_to_sync")

        mock_group_send = mock_async_to_sync.return_value

        # Вызов celery-задачи
        send_channel_notify_event(user_id=user.pk, update_list=False)

        mock_async_to_sync.assert_called_once_with(mock_channel_layer.group_send)

        mock_group_send.assert_called_once_with(
            f"user_{user.pk}",
            {
                "type": "notify",
                "unread_notifications_count": 2,
                "update_list": False,
            },
        )
