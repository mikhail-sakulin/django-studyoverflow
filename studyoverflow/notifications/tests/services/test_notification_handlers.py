import pytest

from notifications.models import Notification, NotificationType
from notifications.services.notification_handlers import (
    handle_notification_comment_like,
    handle_notification_comment_on_post_created,
    handle_notification_post_created,
    handle_notification_post_like,
    handle_notification_reply_to_comment_created,
    handle_notification_user_created,
    handle_send_channel_notify_event,
)


@pytest.mark.django_db
class TestNotificationHandlers:
    """Тестирование обработчиков создания уведомлений и запуска celery задач."""

    def test_handle_send_channel_notify_event(
        self, django_capture_on_commit_callbacks, notification_post_factory, mock_notify_dispatch
    ):
        """
        Проверка создания Celery-задачи для отправки обновления счетчика непрочитанных уведомлений.
        """
        notification = notification_post_factory()
        mock_notify_dispatch.reset_mock()

        with django_capture_on_commit_callbacks(execute=True):
            handle_send_channel_notify_event(notification)

        mock_notify_dispatch.assert_called_once_with(
            (),
            {
                "user_id": notification.user_id,
                "update_list": True,
                "reason": "update",
            },
        )

    def test_handle_notification_post_like_other_user(
        self, django_capture_on_commit_callbacks, user_factory, post_factory, like_factory
    ):
        """
        Проверка создания уведомления о лайке поста другим пользователем.
        """
        author = user_factory()
        liker = user_factory(username="liker_user")
        post = post_factory(author=author, title="Мой пост")
        like = like_factory(content_object=post, user=liker)

        with django_capture_on_commit_callbacks(execute=True):
            handle_notification_post_like(like)

        n = Notification.objects.get(user=author, notification_type=NotificationType.LIKE_POST)
        assert n.user == author
        assert n.actor == liker
        assert n.content_object == like
        assert n.message == 'Пользователь liker_user лайкнул ваш пост "Мой пост".'

    def test_handle_notification_post_like_self(
        self, django_capture_on_commit_callbacks, user_factory, post_factory, like_factory
    ):
        """
        Проверка создания уведомления о лайке собственного поста.
        """
        author = user_factory()
        post = post_factory(author=author, title="Мой пост")
        like = like_factory(content_object=post, user=author)

        with django_capture_on_commit_callbacks(execute=True):
            handle_notification_post_like(like)

        n = Notification.objects.get(user=author, notification_type=NotificationType.LIKE_POST)
        assert n.user == author
        assert n.actor == author
        assert n.message == 'Вы лайкнули свой пост "Мой пост".'

    def test_handle_notification_comment_like_other_user(
        self, django_capture_on_commit_callbacks, user_factory, comment_factory, like_factory
    ):
        """Проверка создания уведомления о лайке комментария."""
        author = user_factory()
        liker = user_factory(username="liker_user")
        comment = comment_factory(author=author, content="New Comment")
        like = like_factory(content_object=comment, user=liker)

        with django_capture_on_commit_callbacks(execute=True):
            handle_notification_comment_like(like)

        n = Notification.objects.get(user=author, notification_type=NotificationType.LIKE_COMMENT)
        assert n.user == author
        assert n.actor == liker
        assert n.message == 'Пользователь liker_user лайкнул ваш комментарий "New Comment".'

    def test_handle_notification_comment_like_by_self(
        self, django_capture_on_commit_callbacks, user_factory, comment_factory, like_factory
    ):
        """
        Проверка создания уведомления о лайке собственного комментария.
        """
        author = user_factory()
        comment = comment_factory(author=author, content="New Comment")
        like = like_factory(content_object=comment, user=author)

        with django_capture_on_commit_callbacks(execute=True):
            handle_notification_comment_like(like)

        n = Notification.objects.get(user=author, notification_type=NotificationType.LIKE_COMMENT)
        assert n.message == 'Вы лайкнули свой комментарий "New Comment".'

    def test_handle_notification_post_created(
        self, django_capture_on_commit_callbacks, user_factory, post_factory
    ):
        """Проверка создания уведомления о создании нового поста."""
        author = user_factory()
        post = post_factory(author=author, title="Мой пост")

        with django_capture_on_commit_callbacks(execute=True):
            handle_notification_post_created(post)

        n = Notification.objects.get(user=author, notification_type=NotificationType.POST)
        assert n.user == author
        assert n.actor == author
        assert n.content_object == post
        assert n.message == 'Вы опубликовали новый пост "Мой пост".'

    def test_handle_notification_comment_on_post_created_other(
        self, django_capture_on_commit_callbacks, user_factory, post_factory, comment_factory
    ):
        """Проверка создания уведомления о комментарии к посту."""
        post_author = user_factory()
        commenter = user_factory(username="commenter_user")
        post = post_factory(author=post_author, title="Мой пост")
        comment = comment_factory(post=post, author=commenter, content="Привет")

        with django_capture_on_commit_callbacks(execute=True):
            handle_notification_comment_on_post_created(comment)

        n = Notification.objects.get(user=post_author, notification_type=NotificationType.COMMENT)
        assert n.user == post_author
        assert n.actor == commenter
        assert n.content_object == comment
        assert n.message == (
            'Пользователь commenter_user оставил комментарий "Привет" к вашему посту "Мой пост".'
        )

    def test_comment_on_own_post(
        self, django_capture_on_commit_callbacks, user_factory, post_factory, comment_factory
    ):
        author = user_factory()
        post = post_factory(author=author, title="Мой пост")
        comment = comment_factory(post=post, author=author, content="Привет")

        with django_capture_on_commit_callbacks(execute=True):
            handle_notification_comment_on_post_created(comment)

        n = Notification.objects.get(user=author, notification_type=NotificationType.COMMENT)
        assert n.message == 'Вы оставили комментарий "Привет" к вашему посту "Мой пост".'

    def test_handle_notification_reply_to_comment_created_other(
        self, django_capture_on_commit_callbacks, user_factory, post_factory, comment_factory
    ):
        """
        Проверка создания уведомления об ответе на комментарий от другого пользователя.
        """
        parent_author = user_factory()
        replier = user_factory(username="replier_user")
        post = post_factory()
        parent = comment_factory(post=post, author=parent_author, content="Вопрос")
        reply = comment_factory(
            post=post, author=replier, parent_comment=parent, reply_to=parent, content="Ответ"
        )

        with django_capture_on_commit_callbacks(execute=True):
            handle_notification_reply_to_comment_created(reply)

        n = Notification.objects.get(user=parent_author, notification_type=NotificationType.REPLY)
        assert n.user == parent_author
        assert n.actor == replier
        assert n.content_object == reply
        assert n.message == 'Пользователь replier_user ответил "Ответ" на ваш комментарий "Вопрос".'

    def test_reply_to_own_comment(
        self, django_capture_on_commit_callbacks, user_factory, post_factory, comment_factory
    ):
        author = user_factory()
        post = post_factory()
        parent = comment_factory(post=post, author=author, content="Вопрос")
        reply = comment_factory(
            post=post, author=author, parent_comment=parent, reply_to=parent, content="Ответ"
        )

        with django_capture_on_commit_callbacks(execute=True):
            handle_notification_reply_to_comment_created(reply)

        n = Notification.objects.get(user=author, notification_type=NotificationType.REPLY)
        assert n.message == 'Вы ответили "Ответ" на ваш комментарий "Вопрос".'

    def test_handle_notification_user_created(
        self, user_factory, django_capture_on_commit_callbacks
    ):
        """
        Проверка создания приветственного уведомления об успешной регистрации пользователя.
        """
        user = user_factory()

        with django_capture_on_commit_callbacks(execute=True):
            handle_notification_user_created(user)

        n = Notification.objects.get(user=user, notification_type=NotificationType.REGISTER)
        assert n.user == user
        assert n.actor == user
        assert n.content_object == user
        assert n.message == "Вы успешно зарегистрировались!"
