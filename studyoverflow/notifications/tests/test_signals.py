import pytest
from django.contrib.auth import get_user_model

from posts.models import Like


User = get_user_model()


@pytest.mark.django_db
class TestLikeSignals:
    """Тестирование сигналов при создании лайков."""

    def test_like_on_post_triggers_signal(self, user_factory, post_factory, mocker):
        """Создание лайка на пост вызывает свой handler."""
        mock_handler = mocker.patch("notifications.signals.handle_notification_post_like")

        user = user_factory()
        post = post_factory()
        like = Like.objects.create(content_object=post, user=user)

        mock_handler.assert_called_once_with(like)

    def test_like_on_comment_triggers_signal(self, user_factory, comment_factory, mocker):
        """Создание лайка на комментарий вызывает нужный обработчик."""
        mock_handler = mocker.patch("notifications.signals.handle_notification_comment_like")

        user = user_factory()
        comment = comment_factory()
        like = Like.objects.create(content_object=comment, user=user)

        mock_handler.assert_called_once_with(like)


@pytest.mark.django_db
class TestPostSignals:
    """Тестирование сигналов при создании постов."""

    def test_post_creation_triggers_signal(self, user_factory, post_factory, mocker):
        """Создание поста вызывает нужный handler."""
        mock_handler = mocker.patch("notifications.signals.handle_notification_post_created")

        post = post_factory()

        mock_handler.assert_called_once_with(post)


@pytest.mark.django_db
class TestCommentSignals:
    """Тестирование сигналов при создании комментариев."""

    def test_root_comment_creation_triggers_signal(
        self, user_factory, post_factory, comment_factory, mocker
    ):
        """Создание родительского комментария вызывает только уведомление автора поста."""
        mock_post_handler = mocker.patch(
            "notifications.signals.handle_notification_comment_on_post_created"
        )
        mock_reply_handler = mocker.patch(
            "notifications.signals.handle_notification_reply_to_comment_created"
        )

        comment = comment_factory()

        mock_post_handler.assert_called_once_with(comment)
        mock_reply_handler.assert_not_called()

    def test_reply_comment_different_authors_triggers_both_signals(
        self, user_factory, post_factory, comment_factory, mocker
    ):
        """Ответ на комментарий уведомляет авторов поста и родительского комментария."""
        mock_post_handler = mocker.patch(
            "notifications.signals.handle_notification_comment_on_post_created"
        )
        mock_reply_handler = mocker.patch(
            "notifications.signals.handle_notification_reply_to_comment_created"
        )

        post_author = user_factory()
        parent_author = user_factory()
        reply_author = user_factory()

        post = post_factory(author=post_author)

        parent_comment = comment_factory(author=parent_author, post=post)

        # Очистка моков перед созданием целевого комментария
        mock_post_handler.reset_mock()
        mock_reply_handler.reset_mock()

        reply_comment = comment_factory(
            author=reply_author, post=post, parent_comment=parent_comment, reply_to=parent_comment
        )

        mock_post_handler.assert_called_once_with(reply_comment)
        mock_reply_handler.assert_called_once_with(reply_comment)

    def test_reply_comment_same_authors_triggers_only_reply_signal(
        self, user_factory, post_factory, comment_factory, mocker
    ):
        """
        Если пользователь отвечает на комментарий автора под постом автора,
        срабатывает только одно уведомление для автора.
        """
        mock_post_handler = mocker.patch(
            "notifications.signals.handle_notification_comment_on_post_created"
        )
        mock_reply_handler = mocker.patch(
            "notifications.signals.handle_notification_reply_to_comment_created"
        )

        post_author = user_factory()
        reply_author = user_factory()
        post = post_factory(author=post_author)

        parent_comment = comment_factory(author=post_author, post=post)

        # Очистка моков перед созданием целевого комментария
        mock_post_handler.reset_mock()
        mock_reply_handler.reset_mock()

        reply_comment = comment_factory(
            author=reply_author, post=post, parent_comment=parent_comment, reply_to=parent_comment
        )

        mock_post_handler.assert_not_called()
        mock_reply_handler.assert_called_once_with(reply_comment)


@pytest.mark.django_db
class TestUserSignals:
    """Тестирование сигналов при регистрации пользователей."""

    def test_user_creation_triggers_signal(self, user_factory, mocker):
        """Регистрация пользователя вызывает создание приветственного уведомления."""
        mock_handler = mocker.patch("notifications.signals.handle_notification_user_created")

        user = user_factory()

        mock_handler.assert_called_once_with(user)


@pytest.mark.django_db
class TestNotificationModelSignals:
    """Тестирование сигналов самой модели Notification (WebSocket и логирование)."""

    def test_notification_creation_triggers_ws(
        self, user_factory, notification_post_factory, mocker
    ):
        """Проверка, что создание уведомления вызывает handler с WebSocket-событием."""
        mock_ws_handler = mocker.patch("notifications.signals.handle_send_channel_notify_event")

        user = user_factory()

        notification = notification_post_factory(user=user)

        mock_ws_handler.assert_called_once_with(notification)

    def test_notification_creation_triggers_logging(
        self, user_factory, notification_post_factory, mocker
    ):
        """Проверка, что создание уведомления логируется."""
        mock_logger = mocker.patch("notifications.signals.logger.info")

        user = user_factory()

        notification_post_factory(user=user)

        mock_logger.assert_called_once()
        log_args, log_kwargs = mock_logger.call_args
        assert "Создано уведомление" in log_args[0]
        assert log_kwargs["extra"]["for_user"] == user.pk

    def test_notification_deletion_triggers_ws(
        self, user_factory, notification_post_factory, mocker
    ):
        """Проверка, что удаление уведомления вызывает handler с WebSocket-событием."""
        mock_ws_handler = mocker.patch("notifications.signals.handle_send_channel_notify_event")

        user = user_factory()
        notification = notification_post_factory(user=user)

        mock_ws_handler.reset_mock()
        notification.delete()

        mock_ws_handler.assert_called_once()
