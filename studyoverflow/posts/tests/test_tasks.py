import pytest

from posts.models import Comment, Like, Post
from posts.tasks import sync_comment_counters, sync_post_counters


@pytest.mark.django_db
class TestSyncCountersTasks:
    def test_sync_post_counters(self, user_factory, post_factory, comment_factory):
        """
        Celery задача корректно пересчитывает количество комментариев и лайков
        для всех постов через единый запрос к БД.
        """
        user1 = user_factory()

        # Пост без комментариев и лайков
        post_empty = post_factory()

        # Пост с 2 комментариями и 1 лайком
        post_active = post_factory()
        comment_factory.create_batch(2, post=post_active)
        Like.objects.create(user=user1, content_object=post_active)

        # Задаются неверные счетчики через update, чтобы не сработали сигналы
        Post.objects.update(comments_count=999, likes_count=999)

        # Запуск celery задачи
        sync_post_counters()

        # Проверка пустого поста
        post_empty.refresh_from_db()
        assert post_empty.comments_count == 0
        assert post_empty.likes_count == 0

        # Проверка не пустого поста
        post_active.refresh_from_db()
        assert post_active.comments_count == 2
        assert post_active.likes_count == 1

    def test_sync_comment_counters(self, user_factory, comment_factory):
        """
        Celery задача корректно пересчитывает количество лайков
        для всех комментариев через единый запрос к БД.
        """
        user1 = user_factory()
        user2 = user_factory()

        # Комментарий без лайков
        comment_empty = comment_factory()

        # Комментарий с 2 лайками
        comment_active = comment_factory()
        Like.objects.create(user=user1, content_object=comment_active)
        Like.objects.create(user=user2, content_object=comment_active)

        # Задается неверный счетчик через update, чтобы не сработали сигналы
        Comment.objects.update(likes_count=999)

        # Запуск celery задачи
        sync_comment_counters()

        # Проверка пустого комментария
        comment_empty.refresh_from_db()
        assert comment_empty.likes_count == 0

        # Проверка активного комментария
        comment_active.refresh_from_db()
        assert comment_active.likes_count == 2
