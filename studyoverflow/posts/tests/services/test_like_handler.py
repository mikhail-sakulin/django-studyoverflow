import pytest

from posts.models import Comment, Like, Post
from posts.services.like_handler import perform_toggle_like


@pytest.mark.django_db
class TestPerformToggleLike:
    """Тестирование сервисной функции переключения лайков."""

    def test_perform_toggle_like_add(self, user_factory, post_factory):
        """Если лайка не было, он создается."""
        liker = user_factory()
        post = post_factory()

        obj, created = perform_toggle_like(liker, Post.objects.all(), post.pk, source="web")

        assert created is True
        assert obj.pk == post.pk
        assert obj.likes_count == 1
        assert Like.objects.is_liked(liker, post)
        post.author.refresh_from_db()
        assert post.author.reputation == 1

    def test_perform_toggle_like_remove(self, user_factory, post_factory):
        """Если лайк уже существовал, он удаляется."""
        liker = user_factory()
        post = post_factory()
        # Создание первого лайка
        perform_toggle_like(liker, Post.objects.all(), post.pk, source="web")

        # Удаление лайка
        obj, created = perform_toggle_like(liker, Post.objects.all(), post.pk, source="web")

        assert created is False
        assert obj.likes_count == 0
        assert not Like.objects.is_liked(liker, post)
        post.author.refresh_from_db()
        assert post.author.reputation == 0

    def test_toggle_like_works_for_comments(self, user_factory, comment_factory):
        """Создание и удаление лайка работает для комментариев."""
        liker = user_factory()
        comment = comment_factory()

        obj, created = perform_toggle_like(liker, Comment.objects.all(), comment.pk, source="api")
        assert (created, obj.likes_count) == (True, 1)

        obj, created = perform_toggle_like(liker, Comment.objects.all(), comment.pk, source="api")
        assert (created, obj.likes_count) == (False, 0)

    def test_likes_of_different_users_are_independent(self, user_factory, post_factory):
        """Лайки разных пользователей независимы друг от друга."""
        user_1 = user_factory()
        user_2 = user_factory()
        post = post_factory()

        perform_toggle_like(user_1, Post.objects.all(), post.pk, source="web")
        obj, _ = perform_toggle_like(user_2, Post.objects.all(), post.pk, source="web")
        assert Like.objects.is_liked(user_1, post)
        assert Like.objects.is_liked(user_2, post)
        assert obj.likes_count == 2

        obj, _ = perform_toggle_like(user_1, Post.objects.all(), post.pk, source="web")
        assert obj.likes_count == 1
        assert not Like.objects.is_liked(user_1, post)
        assert Like.objects.is_liked(user_2, post)

    def test_missing_object_raises_does_not_exist(self, user_factory):
        """Если объекта не существует, вызывается DoesNotExist."""
        with pytest.raises(Post.DoesNotExist):
            perform_toggle_like(user_factory(), Post.objects.all(), 100, source="web")

    def test_logs_like_events(self, mocker, user_factory, post_factory):
        """Создание и удаление лайков пишутся в логи."""
        liker = user_factory()
        post = post_factory()

        mock_log = mocker.patch("posts.services.like_handler.log_like_event")

        source = "web"

        # Создание лайка
        perform_toggle_like(liker, Post.objects.all(), post.pk, source="web")
        # Удаление лайка
        perform_toggle_like(liker, Post.objects.all(), post.pk, source="web")

        # Проверка логирования
        mock_log.assert_has_calls(
            [
                mocker.call(event_type="like_add", obj=post, user=liker, source=source),
                mocker.call(event_type="like_remove", obj=post, user=liker, source=source),
            ]
        )
