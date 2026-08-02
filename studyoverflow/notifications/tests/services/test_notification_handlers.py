import pytest
from django.contrib.contenttypes.models import ContentType

from notifications.models import Notification, NotificationType
from notifications.services import (
    handle_notification_comment_like,
    handle_notification_comment_on_post_created,
    handle_notification_post_created,
    handle_notification_post_like,
    handle_notification_reply_to_comment_created,
    handle_notification_user_created,
    handle_send_channel_notify_event,
)
from posts.models import Comment, Like, Post


@pytest.fixture(autouse=True)
def mock_transaction_on_commit(mocker):
    """Мок transaction.on_commit, чтобы celery задачи выполнялись сразу в тестах."""
    return mocker.patch(
        "notifications.services.notification_handlers.transaction.on_commit",
        side_effect=lambda func: func(),
    )


@pytest.fixture(autouse=True)
def mock_celery_task_create_notification(mocker):
    """
    Поскольку мокается transaction.on_commit, то celery-задачи будут выполняться.

    После создания объектов (пользователя, поста, комментария) через сигналы и слой сервисов
    уведомлений запускается celery-задача, которая использует redis, поэтому она мокается.
    """
    mocker.patch("notifications.services.notification_handlers.create_notification.delay")


@pytest.mark.django_db
class TestNotificationHandlers:
    """Тестирование обработчиков создания уведомлений и запуска celery задач."""

    def test_handle_send_channel_notify_event(self, user_factory, post_factory, mocker):
        """
        Проверка создания celery-задачи для отправки обновления счетчика непрочитанных уведомлений.
        """
        # Мок celery-задачи, которая будет вызываться в тесте
        mock_task = mocker.patch(
            "notifications.services.notification_handlers.send_channel_notify_event.apply_async"
        )

        user = user_factory()
        post = post_factory()

        notification = Notification.objects.create(
            user=user, actor=user, notification_type=NotificationType.POST, content_object=post
        )

        mock_task.reset_mock()

        handle_send_channel_notify_event(notification)

        mock_task.assert_called_once_with(kwargs={"user_id": user.pk})

    def test_handle_notification_post_like_other_user(self, user_factory, post_factory, mocker):
        """
        Проверка создания celery-задачи для создания уведомления о
        лайке поста другим пользователем.
        """
        author = user_factory(username="author_user")
        liker = user_factory(username="liker_user")
        post = post_factory(author=author, title="Python Django Backend")

        like = Like.objects.create(content_object=post, user=liker)

        mock_delay = mocker.patch(
            "notifications.services.notification_handlers.create_notification.delay"
        )

        handle_notification_post_like(like)

        mock_delay.assert_called_once_with(
            user_id=author.pk,
            actor_id=liker.pk,
            message=mocker.ANY,
            notification_type=NotificationType.LIKE_POST,
            content_type_id=ContentType.objects.get_for_model(Like).pk,
            object_id=like.pk,
        )

    def test_handle_notification_post_like_self(self, user_factory, post_factory, mocker):
        """
        Проверка создания celery-задачи для создания уведомления о лайке собственного поста.
        """
        author = user_factory()
        post = post_factory(author=author, title="Self post test")
        like = Like.objects.create(content_object=post, user=author)

        mock_delay = mocker.patch(
            "notifications.services.notification_handlers.create_notification.delay"
        )

        handle_notification_post_like(like)

        mock_delay.assert_called_once_with(
            user_id=author.pk,
            actor_id=author.pk,
            message=mocker.ANY,
            notification_type=NotificationType.LIKE_POST,
            content_type_id=ContentType.objects.get_for_model(Like).pk,
            object_id=like.pk,
        )

    def test_handle_notification_comment_like_other_user(
        self, user_factory, post_factory, comment_factory, mocker
    ):
        """Проверка создания celery-задачи для создания уведомления о лайке комментария."""
        author = user_factory(username="comment_author")
        liker = user_factory(username="comment_liker")
        post = post_factory()
        comment = comment_factory(post=post, author=author, content="Comment text")
        like = Like.objects.create(content_object=comment, user=liker)

        mock_delay = mocker.patch(
            "notifications.services.notification_handlers.create_notification.delay"
        )

        handle_notification_comment_like(like)

        mock_delay.assert_called_once_with(
            user_id=author.pk,
            actor_id=liker.pk,
            message=mocker.ANY,
            notification_type=NotificationType.LIKE_COMMENT,
            content_type_id=ContentType.objects.get_for_model(Like).pk,
            object_id=like.pk,
        )

    def test_handle_notification_post_created(self, user_factory, post_factory, mocker):
        """Проверка создания celery-задачи для создания уведомления о создании нового поста."""
        author = user_factory()
        post = post_factory(author=author, title="New Test Post")

        mock_delay = mocker.patch(
            "notifications.services.notification_handlers.create_notification.delay"
        )

        handle_notification_post_created(post)

        mock_delay.assert_called_once_with(
            user_id=author.pk,
            actor_id=author.pk,
            message=mocker.ANY,
            notification_type=NotificationType.POST,
            content_type_id=ContentType.objects.get_for_model(Post).pk,
            object_id=post.pk,
        )

    def test_handle_notification_comment_on_post_created_other(
        self, user_factory, post_factory, comment_factory, mocker
    ):
        """Проверка создания celery-задачи для создания уведомления о комментарии к посту."""
        post_author = user_factory(username="post_owner")
        commenter = user_factory(username="commenter_user")
        post = post_factory(author=post_author, title="Main Post Title")
        comment = comment_factory(post=post, author=commenter, content="Cool post insight")

        mock_delay = mocker.patch(
            "notifications.services.notification_handlers.create_notification.delay"
        )

        handle_notification_comment_on_post_created(comment)

        mock_delay.assert_called_once_with(
            user_id=post_author.pk,
            actor_id=commenter.pk,
            message=mocker.ANY,
            notification_type=NotificationType.COMMENT,
            content_type_id=ContentType.objects.get_for_model(Comment).pk,
            object_id=comment.pk,
        )

    def test_handle_notification_reply_to_comment_created_other(
        self, user_factory, post_factory, comment_factory, mocker
    ):
        """
        Проверка создания celery-задачи для создания уведомления об ответе на
        комментарий от другого пользователя.
        """
        parent_author = user_factory(username="parent_owner")
        replier = user_factory(username="replier_user")
        post = post_factory()
        parent_comment = comment_factory(
            post=post, author=parent_author, content="Initial comment message"
        )
        reply_comment = comment_factory(
            post=post,
            parent_comment=parent_comment,
            reply_to=parent_comment,
            author=replier,
            content="Reply response text",
        )

        mock_delay = mocker.patch(
            "notifications.services.notification_handlers.create_notification.delay"
        )

        handle_notification_reply_to_comment_created(reply_comment)

        mock_delay.assert_called_once_with(
            user_id=parent_author.pk,
            actor_id=replier.pk,
            message=mocker.ANY,
            notification_type=NotificationType.REPLY,
            content_type_id=ContentType.objects.get_for_model(Comment).pk,
            object_id=reply_comment.pk,
        )

    def test_handle_notification_user_created(self, user_factory, mocker):
        """
        Проверка создания celery-задачи для создания приветственного уведомления об
        успешной регистрации пользователя.
        """
        user = user_factory()

        mock_delay = mocker.patch(
            "notifications.services.notification_handlers.create_notification.delay"
        )

        handle_notification_user_created(user)

        mock_delay.assert_called_once_with(
            user_id=user.pk,
            actor_id=user.pk,
            message=mocker.ANY,
            notification_type=NotificationType.REGISTER,
            content_type_id=ContentType.objects.get_for_model(type(user)).pk,
            object_id=user.pk,
        )
