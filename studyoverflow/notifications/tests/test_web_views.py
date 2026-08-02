import pytest
from django.urls import reverse

from notifications.models import Notification


@pytest.mark.django_db
class TestNotificationTemplateView:
    def test_unauthenticated_redirect(self, assert_login_required):
        """GET-запрос без авторизации перенаправляет на страницу логина."""
        assert_login_required(url_name="notifications:base", method="get")

    def test_accessible_for_authenticated_user(self, client, user_factory):
        """Авторизованный пользователь получает статус 200."""
        user = user_factory()
        client.force_login(user)

        url = reverse("notifications:base")
        response = client.get(url)

        assert response.status_code == 200
        assert "notifications/notification_base.html" in [t.name for t in response.templates]


@pytest.mark.django_db
class TestNotificationListView:
    def test_unauthenticated_redirect(self, assert_login_required):
        """GET-запрос без авторизации перенаправляет на страницу логина."""
        assert_login_required(url_name="notifications:list", method="get")

    def test_list_returns_only_current_user_notifications(
        self, client, user_factory, notification_post_factory
    ):
        """В контекст попадают только уведомления текущего пользователя."""
        user = user_factory()
        other_user = user_factory()

        # Уведомление для текущего пользователя
        notification_post_factory(user=user)
        # Уведомление для другого пользователя
        notification_post_factory(user=other_user)

        client.force_login(user)
        url = reverse("notifications:list")
        response = client.get(url)

        assert response.status_code == 200
        assert "notifications/_notification_list.html" in [t.name for t in response.templates]

        notification_list = response.context["notification_list"]
        assert len(notification_list) == 1
        assert notification_list[0].user == user


@pytest.mark.django_db
class TestNotificationMarkReadView:
    def test_unauthenticated_redirect(
        self, assert_login_required, user_factory, notification_post_factory
    ):
        """POST-запрос без авторизации перенаправляет на страницу логина."""
        user = user_factory()
        notification = notification_post_factory(user=user)
        assert_login_required(
            url_name="notifications:mark_read",
            url_kwargs={"pk": notification.pk},
            method="post",
        )

    def test_nonexistent_notification_returns_404(self, client, user_factory, assert_not_found):
        """Для несуществующего уведомления возвращается 404."""
        client.force_login(user_factory())
        assert_not_found(
            "notifications:mark_read",
            url_kwargs={"pk": 9999},
            method="post",
            is_api=False,
        )

    def test_forbidden_for_other_user(self, client, user_factory, notification_post_factory):
        """Попытка прочитать чужое уведомление возвращает 403 Forbidden."""
        owner = user_factory()
        other_user = user_factory()

        notification = notification_post_factory(user=owner)

        client.force_login(other_user)
        url = reverse("notifications:mark_read", kwargs={"pk": notification.pk})
        response = client.post(url)

        assert response.status_code == 403
        notification.refresh_from_db()
        assert notification.is_read is False

    def test_mark_read_success(self, client, user_factory, notification_post_factory):
        """Пользователь успешно помечает свое уведомление прочитанным."""
        user = user_factory()

        notification = notification_post_factory(user=user)

        client.force_login(user)
        url = reverse("notifications:mark_read", kwargs={"pk": notification.pk})
        response = client.post(url)

        assert response.status_code == 200
        notification.refresh_from_db()
        assert notification.is_read is True


@pytest.mark.django_db
class TestNotificationMarkAllReadView:
    def test_unauthenticated_redirect(self, assert_login_required):
        """POST-запрос без авторизации перенаправляет на страницу логина."""
        assert_login_required(url_name="notifications:mark_all_read", method="post")

    def test_mark_all_read_success_and_triggers_celery(
        self, client, user_factory, notification_post_factory, mocker
    ):
        """
        Все непрочитанные уведомления пользователя становятся прочитанными,
        запускается celery задача.
        """
        mock_task = mocker.patch("notifications.views.send_channel_notify_event.delay")

        user = user_factory()
        other_user = user_factory()

        n1 = notification_post_factory(user=user)
        n2 = notification_post_factory(user=user)
        n_other = notification_post_factory(user=other_user)

        client.force_login(user)
        url = reverse("notifications:mark_all_read")
        response = client.post(url)

        assert response.status_code == 200

        n1.refresh_from_db()
        n2.refresh_from_db()
        n_other.refresh_from_db()

        assert n1.is_read is True
        assert n2.is_read is True
        assert n_other.is_read is False

        mock_task.assert_called_once_with(user_id=user.pk, update_list=False)


@pytest.mark.django_db
class TestNotificationDeleteView:
    def test_unauthenticated_redirect(
        self, assert_login_required, user_factory, notification_post_factory
    ):
        """POST-запрос без авторизации перенаправляет на страницу логина."""
        user = user_factory()
        notification = notification_post_factory(user=user)
        assert_login_required(
            url_name="notifications:delete",
            url_kwargs={"pk": notification.pk},
            method="post",
        )

    def test_nonexistent_notification_returns_404(self, client, user_factory, assert_not_found):
        """Для несуществующего уведомления возвращается 404."""
        client.force_login(user_factory())
        assert_not_found(
            "notifications:delete",
            url_kwargs={"pk": 9999},
            method="post",
            is_api=False,
        )

    def test_forbidden_for_other_user(self, client, user_factory, notification_post_factory):
        """Удаление чужого уведомления запрещено, возвращается 403."""
        owner = user_factory()
        other_user = user_factory()

        notification = notification_post_factory(user=owner)

        client.force_login(other_user)
        url = reverse("notifications:delete", kwargs={"pk": notification.pk})
        response = client.post(url)

        assert response.status_code == 403
        assert Notification.objects.filter(pk=notification.pk).exists() is True

    def test_delete_notification_success(self, client, user_factory, notification_post_factory):
        """Владелец может удалить свое уведомление."""
        user = user_factory()

        notification = notification_post_factory(user=user)

        client.force_login(user)
        url = reverse("notifications:delete", kwargs={"pk": notification.pk})
        response = client.post(url)

        assert response.status_code == 200
        assert not Notification.objects.filter(pk=notification.pk).exists()


@pytest.mark.django_db
class TestNotificationDeleteAllView:
    def test_unauthenticated_redirect(self, assert_login_required):
        """POST-запрос без авторизации перенаправляет на страницу логина."""
        assert_login_required(url_name="notifications:delete_all", method="post")

    def test_delete_all_empty_queryset(self, client, user_factory):
        """Проверка работы view, если у пользователя нет уведомлений."""
        user = user_factory()

        client.force_login(user)
        url = reverse("notifications:delete_all")
        response = client.post(url)

        assert response.status_code == 200

    def test_delete_all_notifications_success(
        self, client, user_factory, notification_post_factory
    ):
        """Удаляются только уведомления текущего пользователя."""
        user = user_factory()
        other_user = user_factory()

        notification_post_factory(user=user)
        notification_post_factory(user=user)
        other_notification = notification_post_factory(user=other_user)

        client.force_login(user)
        url = reverse("notifications:delete_all")
        response = client.post(url)

        assert response.status_code == 200

        assert not Notification.objects.filter(user=user).exists()
        assert Notification.objects.filter(pk=other_notification.pk).exists()
