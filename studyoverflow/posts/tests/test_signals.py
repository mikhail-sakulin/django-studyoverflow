import pytest

from posts.models import Like


@pytest.mark.django_db
class TestUserCountersSignals:
    """Тестирование вызовов сервиса обновления счетчиков пользователя."""

    def test_post_create_and_delete_updates_author_posts_count(
        self, user_factory, post_factory, mocker
    ):
        """При создании и удалении поста изменяется счетчик posts_count у автора."""
        mock_update = mocker.patch("posts.signals.update_user_counter_field")
        user = user_factory()

        # Создание поста
        post = post_factory(author=user)
        mock_update.assert_called_with(user.pk, "posts_count", 1)

        # Обновление поста не увеличивает счетчик
        mock_update.reset_mock()
        post.title = "Новый заголовок"
        post.save()
        mock_update.assert_not_called()

        # Удаление поста
        post.delete()
        mock_update.assert_called_with(user.pk, "posts_count", -1)

    def test_comment_create_and_delete_updates_author_comments_count(
        self, user_factory, comment_factory, mocker
    ):
        """
        При создании и удалении комментария изменяется счетчик comments_count у автора комментария.
        """
        mock_update = mocker.patch("posts.signals.update_user_counter_field")
        user = user_factory()

        comment = comment_factory(author=user)
        mock_update.assert_called_with(user.pk, "comments_count", 1)

        comment.delete()
        mock_update.assert_called_with(user.pk, "comments_count", -1)

    def test_post_like_create_and_delete_updates_author_reputation(
        self, user_factory, post_factory, mocker
    ):
        """При лайке поста у автора поста изменяется репутация."""
        mock_update = mocker.patch("posts.signals.update_user_counter_field")

        author = user_factory()
        post = post_factory(author=author)
        user_liker = user_factory()

        # Очистка истории вызовов мока, чтобы затем проверить еще один его вызов
        mock_update.reset_mock()
        like = Like.objects.create(user=user_liker, content_object=post)
        mock_update.assert_called_with(author.pk, "reputation", 1)

        like.delete()
        mock_update.assert_called_with(author.pk, "reputation", -1)

    def test_comment_like_create_and_delete_updates_author_reputation(
        self, user_factory, comment_factory, mocker
    ):
        """При лайке комментария у автора поста изменяется репутация."""
        mock_update = mocker.patch("posts.signals.update_user_counter_field")

        author = user_factory()
        comment = comment_factory(author=author)
        user_liker = user_factory()

        # Очистка истории вызовов мока, чтобы затем проверить еще один его вызов
        mock_update.reset_mock()
        like = Like.objects.create(user=user_liker, content_object=comment)
        mock_update.assert_called_with(author.pk, "reputation", 1)

        like.delete()
        mock_update.assert_called_with(author.pk, "reputation", -1)


@pytest.mark.django_db
class TestObjectCountersSignals:
    """
    Тестирование обновления полей likes_count у комментария и поста и
    comments_count у поста.
    """

    def test_comment_create_and_delete_updates_post_comments_count(
        self, post_factory, comment_factory
    ):
        """Создание и удаление комментария обновляет comments_count связанного поста."""
        post = post_factory()
        assert post.comments_count == 0

        # Создание комментария
        comment = comment_factory(post=post)
        post.refresh_from_db()
        assert post.comments_count == 1

        # Создание дочернего комментария
        child_comment = comment_factory(post=post, parent_comment=comment, reply_to=comment)
        post.refresh_from_db()
        assert post.comments_count == 2

        # Удаление комментариев
        comment.delete()
        child_comment.delete()
        post.refresh_from_db()
        assert post.comments_count == 0

    def test_like_create_and_delete_updates_post_likes_count(self, post_factory, user_factory):
        """Создание и удаление лайка обновляет likes_count поста."""
        post = post_factory()
        user = user_factory()
        assert post.likes_count == 0

        # Создание лайка
        like = Like.objects.create(user=user, content_object=post)
        post.refresh_from_db()
        assert post.likes_count == 1

        # Удаление лайка
        like.delete()
        post.refresh_from_db()
        assert post.likes_count == 0

    def test_like_create_and_delete_updates_comment_likes_count(
        self, comment_factory, user_factory
    ):
        """Создание и удаление лайка обновляет likes_count комментария."""
        comment = comment_factory()
        user = user_factory()
        assert comment.likes_count == 0

        # Создание лайка
        like = Like.objects.create(user=user, content_object=comment)
        comment.refresh_from_db()
        assert comment.likes_count == 1

        # Удаление лайка
        like.delete()
        comment.refresh_from_db()
        assert comment.likes_count == 0
