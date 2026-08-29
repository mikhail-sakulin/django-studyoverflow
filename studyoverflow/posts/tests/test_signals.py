import pytest

from posts.models import LowercaseTag


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
        self, user_factory, post_factory, like_factory, mocker
    ):
        """При лайке поста у автора поста изменяется репутация."""
        mock_update = mocker.patch("posts.signals.update_user_counter_field")

        author = user_factory()
        post = post_factory(author=author)
        user_liker = user_factory()

        # Очистка истории вызовов мока, чтобы затем проверить еще один его вызов
        mock_update.reset_mock()
        like = like_factory(user=user_liker, content_object=post)
        mock_update.assert_called_with(author.pk, "reputation", 1)

        like.delete()
        mock_update.assert_called_with(author.pk, "reputation", -1)

    def test_comment_like_create_and_delete_updates_author_reputation(
        self, user_factory, comment_factory, like_factory, mocker
    ):
        """При лайке комментария у автора поста изменяется репутация."""
        mock_update = mocker.patch("posts.signals.update_user_counter_field")

        author = user_factory()
        comment = comment_factory(author=author)
        user_liker = user_factory()

        # Очистка истории вызовов мока, чтобы затем проверить еще один его вызов
        mock_update.reset_mock()
        like = like_factory(user=user_liker, content_object=comment)
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

    def test_like_create_and_delete_updates_post_likes_count(
        self, post_factory, user_factory, like_factory
    ):
        """Создание и удаление лайка обновляет likes_count поста."""
        post = post_factory()
        user = user_factory()
        assert post.likes_count == 0

        # Создание лайка
        like = like_factory(user=user, content_object=post)
        post.refresh_from_db()
        assert post.likes_count == 1

        # Удаление лайка
        like.delete()
        post.refresh_from_db()
        assert post.likes_count == 0

    def test_like_create_and_delete_updates_comment_likes_count(
        self, comment_factory, user_factory, like_factory
    ):
        """Создание и удаление лайка обновляет likes_count комментария."""
        comment = comment_factory()
        user = user_factory()
        assert comment.likes_count == 0

        # Создание лайка
        like = like_factory(user=user, content_object=comment)
        comment.refresh_from_db()
        assert comment.likes_count == 1

        # Удаление лайка
        like.delete()
        comment.refresh_from_db()
        assert comment.likes_count == 0


@pytest.mark.django_db
class TestPostCacheSignals:

    def test_post_cache_invalidation_on_update_and_delete(self, post_factory, mocker):
        """
        При создании поста кэш не сбрасывается.

        При обновлении и удалении поста вызывается сервис удаления кэша.
        """
        mock_delete_cache = mocker.patch("posts.signals.delete_cache_post_detail")

        # 1) Создание поста (created=True) — кэш не сбрасывается
        post = post_factory()
        mock_delete_cache.assert_not_called()

        # 2) Обновление поста (created=False) — кэш сбрасывается
        post.title = "Обновленный заголовок"
        post.save()
        mock_delete_cache.assert_called_once_with(post.pk)

        # 3) Удаление поста — кэш сбрасывается
        mock_delete_cache.reset_mock()
        post_id = post.pk
        post.delete()
        mock_delete_cache.assert_called_once_with(post_id)


@pytest.mark.django_db
class TestTagCacheSignals:

    def test_tags_cache_invalidation_on_create_update_and_delete(self, mocker):
        """
        При создании, изменении и удалении тега вызывается сервис удаления кеша списка тегов.
        """
        mock_delete_cache = mocker.patch("posts.signals.delete_cache_tags_list")

        # 1) Создание тега — кеш сбрасывается
        tag = LowercaseTag.objects.create(name="python")
        mock_delete_cache.assert_called_once()

        # 2) Обновление тега — кеш сбрасывается
        mock_delete_cache.reset_mock()
        tag.name = "django"
        tag.save()
        mock_delete_cache.assert_called_once()

        # 3) Удаление тега — кеш сбрасывается
        mock_delete_cache.reset_mock()
        tag.delete()
        mock_delete_cache.assert_called_once()


@pytest.mark.django_db
class TestTagPostsCountSignals:

    def test_tag_posts_count_increases_and_cache_invalidated_on_post_creation(
        self, post_factory, mocker
    ):
        """
        При создании поста с тегами у каждого тега увеличивается posts_count
        и сбрасывается кеш списка тегов.
        """
        mock_delete_cache = mocker.patch("posts.signals.delete_cache_tags_list")

        # Теги создаются заранее, чтобы можно было сделать reset mock_delete_cache.reset_mock()
        # после создания тегов. Тогда можно будет проверить, что мок mock_delete_cache вызывался
        # именно при назначении тегов посту.
        LowercaseTag.objects.create(name="python")
        LowercaseTag.objects.create(name="django")

        mock_delete_cache.reset_mock()

        post_factory(tags=["python", "django"])

        tag_python = LowercaseTag.objects.get(name="python")
        tag_django = LowercaseTag.objects.get(name="django")
        assert tag_python.posts_count == 1
        assert tag_django.posts_count == 1
        assert mock_delete_cache.call_count == 2

    def test_tag_posts_count_increases_for_multiple_posts_with_same_tag(self, post_factory):
        """При создании нескольких постов с одинаковым тегом posts_count суммируется."""
        post_factory(tags=["python"])
        post_factory(tags=["python"])

        tag = LowercaseTag.objects.get(name="python")
        assert tag.posts_count == 2

    def test_tag_posts_count_decreases_and_cache_invalidated_on_post_delete(
        self, post_factory, mocker
    ):
        """При удалении поста posts_count связанного тега уменьшается и сбрасывается кеш."""
        post = post_factory(tags=["python"])
        tag = LowercaseTag.objects.get(name="python")
        assert tag.posts_count == 1

        mock_delete_cache = mocker.patch("posts.signals.delete_cache_tags_list")
        post.delete()

        tag.refresh_from_db()
        assert tag.posts_count == 0
        mock_delete_cache.assert_called_once()
