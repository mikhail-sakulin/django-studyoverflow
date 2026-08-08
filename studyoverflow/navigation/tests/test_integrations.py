"""
Интеграционные тесты взаимодействия объектов моделей проекта studyoverflow.

Проверяют взаимодействие объектов моделей User, Post, Comment, Like и Notification, а также
ORM, сигналы и Celery-задачи в сценариях создания, редактирования и удаления постов, комментариев
и лайков.
"""

from collections import Counter, defaultdict

import pytest

from notifications.models import Notification, NotificationType
from posts.models import Comment, Like, Post


def assert_notification(user, notification_type, object_id=None, count=1):
    """Проверяет, что для пользователя создано ровно count уведомлений указанного типа."""
    qs = Notification.objects.filter(user=user, notification_type=notification_type)

    if object_id is not None:
        qs = qs.filter(object_id=object_id)

    actual = qs.count()
    assert actual == count, (
        f"Ожидалось {count}, а найдено {actual} уведомлений {notification_type.label} "
        f"для {user.username}."
    )


def assert_no_notification(user, notification_type, object_id=None):
    """Проверяет, что уведомление указанного типа отсутствует у пользователя."""
    qs = Notification.objects.filter(user=user, notification_type=notification_type)
    if object_id is not None:
        qs = qs.filter(object_id=object_id)
    assert (
        not qs.exists()
    ), f"Уведомление {notification_type.label} для {user.username} не должно существовать."


@pytest.fixture(autouse=True)
def mock_notify_dispatch(mocker):
    """
    Мок celery задачи отправки обновления счетчика непрочитанных уведомлений через websocket.

    Данная celery задача вызывается при создании уведомления в другой celery-задаче.
    """
    return mocker.patch("notifications.tasks.send_channel_notify_event.apply_async")


@pytest.mark.django_db
class TestFullUserPostCommentLikeActions:
    """
    Интеграционное тестирование полного жизненного цикла взаимодействия пользователей,
    задействует модели User, Post, Comment, Like и Notification.

    В ходе теста проверяется:
    1) Создание пользователей, проверка денормализованных счетчиков пользователей.
    2) Создание постов, проверка денормализованных счетчиков постов.
    3) Создание комментариев: родительского и дочернего, проверка денормализованных счетчиков
       комментариев.
    4) Создание лайков к посту и к комментариям.
    5) Автоматическое создание уведомлений на различные действия пользователей, проверка типов и
       количества уведомлений.
    6) Вызовы celery-задачи обновления счетчиков комментариев.
    """

    def test_full_interaction_lifecycle(
        self,
        django_capture_on_commit_callbacks,
        user_factory,
        post_factory,
        comment_factory,
        like_factory,
        mock_notify_dispatch,
    ):
        # Словарь с user_pk пользователей, для которых будут создаваться уведомления,
        # используется для подсчета количества вызовов celery-задачи обновления счетчика
        # уведомлений для каждого пользователя, чтобы затем сравнить данные с данными
        # вызовов мока celery-задачи
        expected_notify_dispatch_calls: defaultdict[int, int] = defaultdict(int)

        # 1) Создание пользователей
        # Celery-задача создания уведомления вызывается в сервисе notifications через
        # transaction.on_commit, поэтому используется данный контекстный менеджер, чтобы
        # уведомление создавалось сразу, в настройках CELERY_TASK_ALWAYS_EAGER = True.
        with django_capture_on_commit_callbacks(execute=True):
            user_a = user_factory(username="user_a")
            expected_notify_dispatch_calls[user_a.pk] += 1

            user_b = user_factory(username="user_b")
            expected_notify_dispatch_calls[user_b.pk] += 1

        # Проверка создания уведомлений о регистрации пользователей
        assert_notification(user_a, NotificationType.REGISTER)
        assert_notification(user_b, NotificationType.REGISTER)

        # 2) Создание поста пользователем A
        with django_capture_on_commit_callbacks(execute=True):
            post = post_factory(author=user_a)
            expected_notify_dispatch_calls[user_a.pk] += 1

        user_a.refresh_from_db()
        assert user_a.posts_count == 1
        assert user_a.reputation == 0
        assert_notification(user_a, NotificationType.POST, object_id=post.pk)

        # 3) Комментарий к посту от пользователя B
        with django_capture_on_commit_callbacks(execute=True):
            root_comment = comment_factory(post=post, author=user_b)
            expected_notify_dispatch_calls[user_a.pk] += 1

        post.refresh_from_db()
        user_b.refresh_from_db()
        assert post.comments_count == 1
        assert user_b.comments_count == 1
        assert_notification(user_a, NotificationType.COMMENT, object_id=root_comment.pk)

        # 4) A отвечает на комментарий B
        with django_capture_on_commit_callbacks(execute=True):
            reply_comment = comment_factory(
                post=post, author=user_a, parent_comment=root_comment, reply_to=root_comment
            )
            expected_notify_dispatch_calls[user_b.pk] += 1

        post.refresh_from_db()
        user_a.refresh_from_db()
        assert post.comments_count == 2
        assert user_a.comments_count == 1
        assert_notification(user_b, NotificationType.REPLY, object_id=reply_comment.pk)
        assert_no_notification(user_a, NotificationType.COMMENT, object_id=reply_comment.pk)

        # 5) B лайкает пост от A
        with django_capture_on_commit_callbacks(execute=True):
            post_like = like_factory(user=user_b, content_object=post)
            expected_notify_dispatch_calls[user_a.pk] += 1

        post.refresh_from_db()
        user_a.refresh_from_db()
        assert user_a.reputation == 1

        assert_notification(user_a, NotificationType.LIKE_POST, object_id=post_like.pk)

        assert post.likes_count == 1
        # 6) B лайкает комментарий от A
        with django_capture_on_commit_callbacks(execute=True):
            reply_comment_like = like_factory(user=user_b, content_object=reply_comment)
            expected_notify_dispatch_calls[user_a.pk] += 1

        reply_comment.refresh_from_db()
        user_a.refresh_from_db()
        assert reply_comment.likes_count == 1
        assert user_a.reputation == 2
        assert user_b.reputation == 0

        assert_notification(user_a, NotificationType.LIKE_COMMENT, object_id=reply_comment_like.pk)

        # Проверка, сколько раз вызывалась замоканная celery-задача обновления счетчика
        # непрочитанных уведомлений (при создании уведомлений) для каждого пользователя
        actual_notify_dispatch_calls = [
            call_args.kwargs.get("kwargs", {}).get("user_id")
            for call_args in mock_notify_dispatch.call_args_list
        ]
        assert Counter(actual_notify_dispatch_calls) == expected_notify_dispatch_calls

        # Очистка данных вызовов мока
        mock_notify_dispatch.reset_mock()
        # Очистка словаря с количествами уведомлений пользователей
        expected_notify_dispatch_calls.clear()

        # 7) B снимает лайк с поста
        with django_capture_on_commit_callbacks(execute=True):
            post_like.delete()
            expected_notify_dispatch_calls[user_a.pk] += 1

        post.refresh_from_db()
        user_a.refresh_from_db()
        assert post.likes_count == 0
        assert user_a.reputation == 1

        assert not Like.objects.filter(pk=post_like.pk).exists()
        assert_no_notification(user_a, NotificationType.LIKE_POST, object_id=post_like.pk)

        celery_remove_calls = [
            c.kwargs.get("kwargs", {}).get("user_id") for c in mock_notify_dispatch.call_args_list
        ]
        assert Counter(celery_remove_calls) == expected_notify_dispatch_calls


@pytest.mark.django_db
class TestCascadeDeletion:
    """
    Интеграционные тесты каскадных удалений объектов с участием моделей
    User, Post, Comment, Like и Notification.
    """

    def test_deleting_root_comment_cascades_delete_whole_branch(
        self,
        django_capture_on_commit_callbacks,
        user_factory,
        post_factory,
        comment_factory,
        like_factory,
    ):
        """
        Проверяет каскадное удаление комментариев, лайков и уведомлений при удалении
        родительского комментария.
        """
        # 1) Создание пользователей
        user_a = user_factory(username="user_a")
        user_b = user_factory(username="user_b")

        # 2) Создание поста, комментариев и лайков
        with django_capture_on_commit_callbacks(execute=True):
            post = post_factory(author=user_a)
            root_comment = comment_factory(post=post, author=user_b)
            reply_1 = comment_factory(
                post=post, author=user_a, parent_comment=root_comment, reply_to=root_comment
            )
            reply_2 = comment_factory(
                post=post, author=user_b, parent_comment=root_comment, reply_to=reply_1
            )

            # A лайкает свой пост
            like_factory(user=user_a, content_object=post)

            # A лайкает комментарий B
            like_root_comment = like_factory(user=user_a, content_object=root_comment)

            # B лайкает комментарий A
            like_reply_1 = like_factory(user=user_b, content_object=reply_1)

            # B лайкает свой комментарий
            like_reply_2 = like_factory(user=user_b, content_object=reply_2)

        post.refresh_from_db()
        user_a.refresh_from_db()
        user_b.refresh_from_db()

        assert post.comments_count == 3
        assert user_a.reputation == 2
        assert user_a.comments_count == 1
        assert user_b.reputation == 2
        assert user_b.comments_count == 2

        # Проверка существования некоторых уведомлений
        assert_notification(user_a, NotificationType.POST, count=1)
        assert_notification(user_a, NotificationType.LIKE_COMMENT, count=1)
        assert_notification(user_a, NotificationType.LIKE_POST, count=1)
        assert_notification(user_a, NotificationType.COMMENT, count=1)
        assert_notification(user_a, NotificationType.REPLY, count=1)
        assert_notification(user_b, NotificationType.LIKE_COMMENT, count=2)

        # 3) B удаляет свой root_comment к посту A - должны удалиться дочерние комментарии,
        # соответствующие лайки и уведомления
        with django_capture_on_commit_callbacks(execute=True):
            root_comment.delete()

        # Проверка удаления комментариев и лайков комментариев как объектов
        assert not Comment.objects.filter(pk__in=[root_comment.pk, reply_1.pk, reply_2.pk]).exists()
        assert not Like.objects.filter(
            pk__in=[like_root_comment.pk, like_reply_1.pk, like_reply_2.pk]
        ).exists()

        post.refresh_from_db()
        user_a.refresh_from_db()
        user_b.refresh_from_db()

        assert post.comments_count == 0
        assert user_a.reputation == 1
        assert user_a.comments_count == 0
        assert user_b.reputation == 0
        assert user_b.comments_count == 0

        # Проверка удаления некоторых уведомлений
        assert_no_notification(user_a, NotificationType.LIKE_COMMENT)
        assert_no_notification(user_b, NotificationType.LIKE_COMMENT)
        assert_no_notification(user_a, NotificationType.COMMENT)
        assert_no_notification(user_a, NotificationType.REPLY)

        # Некоторые уведомления остаются
        assert_notification(user_a, NotificationType.POST, count=1)
        assert_notification(user_a, NotificationType.LIKE_POST, count=1)

    def test_deleting_post_cascades_delete_all_objects(
        self,
        django_capture_on_commit_callbacks,
        user_factory,
        post_factory,
        comment_factory,
        like_factory,
    ):
        """
        Проверяет каскадное удаление комментариев, лайков и уведомлений при удалении
        поста.
        """
        # 1) Создание пользователей
        user_a = user_factory(username="user_a")
        user_b = user_factory(username="user_b")

        # 2) Создание поста, комментариев и лайков
        with django_capture_on_commit_callbacks(execute=True):
            post = post_factory(author=user_a)
            root_comment = comment_factory(post=post, author=user_b)
            reply_1 = comment_factory(
                post=post, author=user_a, parent_comment=root_comment, reply_to=root_comment
            )
            reply_2 = comment_factory(
                post=post, author=user_b, parent_comment=root_comment, reply_to=reply_1
            )

            # A лайкает свой пост
            like_post = like_factory(user=user_a, content_object=post)

            # A лайкает комментарий B
            like_root_comment = like_factory(user=user_a, content_object=root_comment)

            # B лайкает комментарий A
            like_reply_1 = like_factory(user=user_b, content_object=reply_1)

            # B лайкает свой комментарий
            like_reply_2 = like_factory(user=user_b, content_object=reply_2)

        # 3) A удаляет свой post - должны удалиться пост, комментарии,
        # соответствующие лайки и уведомления
        with django_capture_on_commit_callbacks(execute=True):
            post.delete()

        # Проверка удаления поста, комментариев и лайков как объектов
        assert not Post.objects.filter(pk__in=[post.pk]).exists()
        assert not Comment.objects.filter(pk__in=[root_comment.pk, reply_1.pk, reply_2.pk]).exists()
        assert not Like.objects.filter(
            pk__in=[like_post.pk, like_root_comment.pk, like_reply_1.pk, like_reply_2.pk]
        ).exists()

        user_a.refresh_from_db()
        user_b.refresh_from_db()

        assert user_a.reputation == 0
        assert user_b.reputation == 0
        assert user_a.comments_count == 0
        assert user_a.posts_count == 0
        assert user_b.comments_count == 0

        # Проверка удаления уведомлений
        assert_no_notification(user_a, NotificationType.POST)
        assert_no_notification(user_a, NotificationType.LIKE_POST)
        assert_no_notification(user_a, NotificationType.LIKE_COMMENT)
        assert_no_notification(user_b, NotificationType.LIKE_COMMENT)
        assert_no_notification(user_a, NotificationType.COMMENT)
        assert_no_notification(user_a, NotificationType.REPLY)

    def test_deleting_one_branch_does_not_affect_other(
        self,
        django_capture_on_commit_callbacks,
        user_factory,
        post_factory,
        comment_factory,
        like_factory,
    ):
        """
        Удаление одной ветки комментариев не затрагивает другую ветку комментариев и
        соответствующие ей лайки и уведомления.
        """
        # 1) Создание пользователей
        user_a = user_factory(username="user_a")
        user_b = user_factory(username="user_b")

        # 2) Создание поста, комментариев и лайков
        with django_capture_on_commit_callbacks(execute=True):
            post = post_factory(author=user_a)

            # Первая ветка комментариев
            root_comment_1 = comment_factory(post=post, author=user_b)
            reply_1 = comment_factory(
                post=post, author=user_a, parent_comment=root_comment_1, reply_to=root_comment_1
            )

            # Вторая ветка комментариев
            root_comment_2 = comment_factory(post=post, author=user_b)
            reply_2 = comment_factory(
                post=post, author=user_a, parent_comment=root_comment_2, reply_to=root_comment_2
            )

            # A лайкает комментарий B root_comment_2
            like_root_comment_2 = like_factory(user=user_a, content_object=root_comment_2)
            # B лайкает комментарий A reply_2
            like_reply_2 = like_factory(user=user_b, content_object=reply_2)

        # 3) B удаляет свой комментарий root_comment_1 - должны удалиться комментарии первой ветки
        #  и соответствующие объекты, а вторая ветка и ее объекты должны остаться
        with django_capture_on_commit_callbacks(execute=True):
            root_comment_1.delete()

        # Проверка удаления комментариев первой ветки
        assert not Comment.objects.filter(pk__in=[root_comment_1.pk, reply_1.pk]).exists()

        # Комментарии и лайки второй ветки остаются
        assert Comment.objects.filter(pk__in=[root_comment_2.pk, reply_2.pk]).exists()
        assert Like.objects.filter(pk__in=[like_root_comment_2.pk, like_reply_2.pk]).exists()

        user_a.refresh_from_db()
        user_b.refresh_from_db()

        assert user_a.reputation == 1
        assert user_b.reputation == 1
        assert user_a.comments_count == 1
        assert user_b.comments_count == 1

        # Проверка уведомлений
        assert_notification(user_a, NotificationType.LIKE_COMMENT, count=1)
        assert_notification(user_b, NotificationType.LIKE_COMMENT, count=1)
        assert_notification(user_a, NotificationType.COMMENT, count=1)
        assert_notification(user_b, NotificationType.REPLY, count=1)
