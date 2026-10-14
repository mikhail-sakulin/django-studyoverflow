import pytest
from django.core.cache import cache

from posts.models import LowercaseTag, Post
from posts.services.cache import (
    get_cached_post,
    get_cached_tags,
    get_post_cache_key,
    get_tags_cache_key,
)


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
class TestUserCountersSignals:
    """Тестирование вызовов сервиса обновления счетчиков пользователя."""

    def test_post_create_and_delete_updates_author_posts_count(self, user_factory, post_factory):
        """При создании и удалении поста изменяется счетчик posts_count у автора."""
        user = user_factory()

        # Создание поста
        post = post_factory(author=user)
        user.refresh_from_db()
        assert user.posts_count == 1

        # Обновление поста не увеличивает счетчик
        post.title = "Новый заголовок"
        post.save()
        user.refresh_from_db()
        assert user.posts_count == 1

        # Удаление поста
        post.delete()
        user.refresh_from_db()
        assert user.posts_count == 0

    def test_comment_create_and_delete_updates_author_comments_count(
        self, user_factory, comment_factory
    ):
        """
        При создании и удалении комментария изменяется счетчик comments_count у автора комментария.
        """
        user = user_factory()

        comment = comment_factory(author=user)
        user.refresh_from_db()
        assert user.comments_count == 1

        comment.delete()
        user.refresh_from_db()
        assert user.comments_count == 0

    @pytest.mark.parametrize("target", ["post", "comment"])
    def test_post_like_create_and_delete_updates_author_reputation(
        self, target, user_factory, post_factory, comment_factory, like_factory
    ):
        """При лайке поста или комментария у автора изменяется репутация."""
        author = user_factory()
        obj = post_factory(author=author) if target == "post" else comment_factory(author=author)

        like = like_factory(user=user_factory(), content_object=obj)
        author.refresh_from_db()
        assert author.reputation == 1

        like.delete()
        author.refresh_from_db()
        assert author.reputation == 0


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

    def _fill_cache(self, post):
        """Создает кеш для поста."""
        get_cached_post(post.pk, Post.objects.all())
        assert cache.get(get_post_cache_key(post.pk)) is not None

    def test_update_invalidates_post_cache(self, post_factory, django_capture_on_commit_callbacks):
        """При обновлении поста кеш инвалидируется."""
        post = post_factory()
        self._fill_cache(post)

        with django_capture_on_commit_callbacks(execute=True):
            post.title = "Обновленный заголовок"
            post.save()

        assert cache.get(get_post_cache_key(post.pk)) is None

    def test_delete_invalidates_post_cache(self, post_factory, django_capture_on_commit_callbacks):
        """При удалении поста кеш инвалидируется."""
        post = post_factory()
        post_pk = post.pk
        self._fill_cache(post)

        with django_capture_on_commit_callbacks(execute=True):
            post.delete()

        assert cache.get(get_post_cache_key(post_pk)) is None

    def test_tags_change_invalidates_post_cache(
        self, post_factory, django_capture_on_commit_callbacks
    ):
        """При изменении тега поста кеш поста инвалидируется."""
        post = post_factory(tags=["first_tag"])
        self._fill_cache(post)

        with django_capture_on_commit_callbacks(execute=True):
            post.tags.add("second_tag")

        assert cache.get(get_post_cache_key(post.pk)) is None


@pytest.mark.django_db
class TestTagCacheSignals:

    def test_tags_cache_invalidation_on_create_update_and_delete(
        self, django_capture_on_commit_callbacks
    ):
        """
        При создании, изменении и удалении тега удаляется кеш списка тегов.
        """
        key = get_tags_cache_key()

        # Создание тега
        get_cached_tags()
        with django_capture_on_commit_callbacks(execute=True):
            tag = LowercaseTag.objects.create(name="python")
        assert cache.get(key) is None

        # Изменение тега
        get_cached_tags()
        assert cache.get(key) is not None
        with django_capture_on_commit_callbacks(execute=True):
            tag.name = "django"
            tag.save()
        assert cache.get(key) is None

        # Удаление тега
        get_cached_tags()
        with django_capture_on_commit_callbacks(execute=True):
            tag.delete()
        assert cache.get(key) is None


@pytest.mark.django_db
class TestTagPostsCountSignals:

    def test_tag_posts_count_increases_and_cache_invalidated_on_post_creation(
        self, post_factory, django_capture_on_commit_callbacks, mocker
    ):
        """
        При создании поста с тегами у каждого тега увеличивается posts_count
        и сбрасывается кеш списка тегов.
        """
        LowercaseTag.objects.create(name="python")
        LowercaseTag.objects.create(name="django")
        get_cached_tags()

        with django_capture_on_commit_callbacks(execute=True):
            post_factory(tags=["python", "django"])

        assert LowercaseTag.objects.get(name="python").posts_count == 1
        assert LowercaseTag.objects.get(name="django").posts_count == 1
        assert cache.get(get_tags_cache_key()) is None

    def test_tag_posts_count_increases_for_multiple_posts_with_same_tag(self, post_factory):
        """При создании нескольких постов с одинаковым тегом posts_count суммируется."""
        post_factory(tags=["python"])
        post_factory(tags=["python"])

        tag = LowercaseTag.objects.get(name="python")
        assert tag.posts_count == 2

    def test_tag_posts_count_decreases_and_cache_invalidated_on_post_delete(
        self, post_factory, django_capture_on_commit_callbacks
    ):
        """При удалении поста posts_count связанного тега уменьшается и сбрасывается кеш."""
        post = post_factory(tags=["python"])
        get_cached_tags()

        with django_capture_on_commit_callbacks(execute=True):
            post.delete()

        assert LowercaseTag.objects.get(name="python").posts_count == 0
        assert cache.get(get_tags_cache_key()) is None
