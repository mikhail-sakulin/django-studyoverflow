import pytest
from django.urls import reverse

from notifications.models import Notification


@pytest.mark.django_db
class TestNotificationViewSet:
    def test_retrieve_nonexistent_notification_returns_404(
        self, assert_not_found, user_factory, api_client
    ):
        """Для несуществующего уведомления возвращается 404."""
        user = user_factory()
        api_client.force_authenticate(user=user)
        assert_not_found(
            "api:notifications:notifications-detail",
            url_kwargs={"pk": 9999},
            method="get",
            is_api=True,
        )

    def test_list_notifications_unauthenticated(self, assert_login_required):
        """Для получения списка уведомлений требуется авторизация, иначе возвращается 401."""
        assert_login_required("api:notifications:notifications-list", method="get", is_api=True)

    def test_list_notifications_returns_only_current_user_notifications(
        self, api_client, user_factory, notification_post_factory
    ):
        """
        В списке возвращаются только уведомления текущего пользователя,
        проверяется фильтрация по is_read.
        """
        user = user_factory()
        other_user = user_factory()

        # Уведомления текущего пользователя
        n_read = notification_post_factory(user=user, is_read=True)
        n_unread = notification_post_factory(user=user, is_read=False)
        # Уведомление другого пользователя
        notification_post_factory(user=other_user, is_read=False)

        api_client.force_authenticate(user=user)
        url = reverse("api:notifications:notifications-list")

        # Получение всех уведомлений пользователя
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.data["count"] == 2

        # Фильтрация по is_read=true
        response_read = api_client.get(url, {"is_read": "true"})
        assert response_read.status_code == 200
        assert response_read.data["count"] == 1
        assert response_read.data["results"][0]["id"] == n_read.pk

        # Фильтрация по is_read=false
        response_unread = api_client.get(url, {"is_read": "false"})
        assert response_unread.status_code == 200
        assert response_unread.data["count"] == 1
        assert response_unread.data["results"][0]["id"] == n_unread.pk

    def test_retrieve_notification_permissions(
        self, api_client, user_factory, notification_post_factory
    ):
        """Получить детали уведомления может только его владелец."""
        owner = user_factory()
        other_user = user_factory()
        notification = notification_post_factory(user=owner)

        url = reverse("api:notifications:notifications-detail", kwargs={"pk": notification.pk})

        # Чужой пользователь -> 404, так как queryset фильтруется по request.user
        api_client.force_authenticate(user=other_user)
        response = api_client.get(url)
        assert response.status_code == 404

        # Владелец -> 200
        api_client.force_authenticate(user=owner)
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.data["id"] == notification.pk

    def test_delete_notification_success(self, api_client, user_factory, notification_post_factory):
        """Владелец может удалить свое уведомление."""
        user = user_factory()
        notification = notification_post_factory(user=user)

        url = reverse("api:notifications:notifications-detail", kwargs={"pk": notification.pk})
        api_client.force_authenticate(user=user)

        response = api_client.delete(url)
        assert response.status_code == 204
        assert not Notification.objects.filter(pk=notification.pk).exists()

    def test_unread_count_action(self, api_client, user_factory, notification_post_factory):
        """Эндпоинт unread-count корректно возвращает количество непрочитанных уведомлений."""
        user = user_factory()
        notification_post_factory(user=user, is_read=False)
        notification_post_factory(user=user, is_read=False)
        notification_post_factory(user=user, is_read=True)

        api_client.force_authenticate(user=user)
        url = reverse("api:notifications:notifications-unread-count")

        response = api_client.get(url)
        assert response.status_code == 200
        assert response.data["unread_count"] == 2

    def test_mark_all_read_action(
        self, api_client, user_factory, notification_post_factory, mocker
    ):
        """Пометка всех уведомлений как прочитанных обновляет статус и запускает celery задачу."""
        mock_task = mocker.patch("notifications.api.views.send_channel_notify_event.delay")

        user = user_factory()
        other_user = user_factory()

        n1 = notification_post_factory(user=user, is_read=False)
        n2 = notification_post_factory(user=user, is_read=False)
        n_other = notification_post_factory(user=other_user, is_read=False)

        api_client.force_authenticate(user=user)
        url = reverse("api:notifications:notifications-mark-all-read")

        response = api_client.post(url)
        assert response.status_code == 200
        assert response.data["detail"] == "Все уведомления помечены прочитанными."

        n1.refresh_from_db()
        n2.refresh_from_db()
        n_other.refresh_from_db()

        assert n1.is_read is True
        assert n2.is_read is True
        assert n_other.is_read is False

        mock_task.assert_called_once_with(user_id=user.pk, update_list=False)

    def test_mark_read_action(self, api_client, user_factory, notification_post_factory):
        """Пометка конкретного уведомления как прочитанного изменяет его статус."""
        user = user_factory()
        notification = notification_post_factory(user=user, is_read=False)

        api_client.force_authenticate(user=user)
        url = reverse("api:notifications:notifications-mark-read", kwargs={"pk": notification.pk})

        response = api_client.patch(url)
        assert response.status_code == 200
        assert response.data["detail"] == "Уведомление изменено на прочитанное."

        notification.refresh_from_db()
        assert notification.is_read is True

    def test_delete_all_action(self, api_client, user_factory, notification_post_factory):
        """Удаление всех уведомлений удаляет записи только текущего пользователя."""
        user = user_factory()
        other_user = user_factory()

        notification_post_factory(user=user)
        notification_post_factory(user=user)
        other_notification = notification_post_factory(user=other_user)

        api_client.force_authenticate(user=user)
        url = reverse("api:notifications:notifications-delete-all")

        response = api_client.delete(url)
        assert response.status_code == 204

        assert not Notification.objects.filter(user=user).exists()
        assert Notification.objects.filter(pk=other_notification.pk).exists()
