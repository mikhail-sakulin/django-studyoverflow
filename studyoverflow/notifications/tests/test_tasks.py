import pytest
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.contenttypes.models import ContentType

from notifications.models import Notification, NotificationType
from notifications.tasks import create_notification, send_channel_notify_event
from posts.models import Post


@pytest.fixture
def channel_layer():
    """InMemoryChannelLayer из настроек тестов, очищенный до и после теста."""
    layer = get_channel_layer()
    async_to_sync(layer.flush)()
    yield layer
    async_to_sync(layer.flush)()


@pytest.fixture
def subscribe_to_user_group(channel_layer):
    """Подписывает новый канал на группу пользователя и возвращает имя канала."""

    def _subscribe(user_id):
        channel_name = async_to_sync(channel_layer.new_channel)()
        async_to_sync(channel_layer.group_add)(f"user_{user_id}", channel_name)
        return channel_name

    return _subscribe


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

    def test_create_notification_object_does_not_exist(self, user_factory):
        """Если целевого объекта (object_id) больше нет в БД, уведомление не создается."""
        user = user_factory()
        content_type = ContentType.objects.get_for_model(Post)
        non_existent_post_id = 100

        create_notification(
            user_id=user.pk,
            actor_id=user.pk,
            message="Тестовое сообщение",
            notification_type=NotificationType.POST.value,  # type: ignore[attr-defined]
            content_type_id=content_type.pk,
            object_id=non_existent_post_id,
        )

        assert not Notification.objects.exists()

    def test_create_notification_content_type_does_not_exist(self, user_factory, mocker):
        """Если ContentType не найден, логгируется warning и уведомление не создается."""
        mock_logger = mocker.patch("notifications.tasks.logger.warning")

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

        assert not Notification.objects.exists()

        mock_logger.assert_called_once()
        (log_msg,) = mock_logger.call_args[0]
        assert "не найден" in log_msg
        assert (
            mock_logger.call_args[1]["extra"]["event_type"] == "notification_content_type_not_found"
        )


@pytest.mark.django_db
class TestSendChannelNotifyEventTask:
    def test_send_event_success_counts_only_unread(
        self,
        user_factory,
        post_factory,
        notification_post_factory,
        channel_layer,
        subscribe_to_user_group,
    ):
        """
        Задача считает только непрочитанные уведомления и отправляет событие в
        Channels-группу пользователя: подписанный канал получает сообщение.
        """
        user = user_factory()
        channel_name = subscribe_to_user_group(user.pk)

        # Создаются 2 непрочитанных и 1 прочитанное уведомление
        notification_post_factory(user=user, is_read=False)
        notification_post_factory(user=user, is_read=False)
        notification_post_factory(user=user, is_read=True)

        send_channel_notify_event(user_id=user.pk, update_list=False)

        message = async_to_sync(channel_layer.receive)(channel_name)
        assert message == {
            "type": "notify",
            "unread_notifications_count": 2,
            "update_list": False,
            "reason": "update",
        }

    def test_send_event_with_explicit_reason(
        self, user_factory, channel_layer, subscribe_to_user_group
    ):
        """Явно переданные update_list и reason попадают в событие, отправленное в группу."""
        user = user_factory()
        channel_name = subscribe_to_user_group(user.pk)

        send_channel_notify_event(user_id=user.pk, update_list=True, reason="self_delete")

        message = async_to_sync(channel_layer.receive)(channel_name)
        assert message == {
            "type": "notify",
            "unread_notifications_count": 0,
            "update_list": True,
            "reason": "self_delete",
        }
