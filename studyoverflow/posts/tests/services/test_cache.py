import pytest
from django.core.cache import cache
from django.db import connection
from django.http import Http404
from django.test.utils import CaptureQueriesContext

from posts.models import LowercaseTag, Post
from posts.services import get_cached_post, get_cached_tags


@pytest.fixture(autouse=True)
def clear_cache():
    """Очищает кеш до и после каждого теста."""
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
class TestGetCachedPost:

    def test_raises_404_for_nonexistent_post(self):
        """Если поста не существует, вызывается 404."""
        queryset = Post.objects.all()
        with pytest.raises(Http404):
            get_cached_post(9999, queryset)

    def test_returns_post_and_populates_cache(self, post_factory):
        """Функция возвращает пост и сохраняет его в кеш."""
        post = post_factory()
        queryset = Post.objects.all()
        cache_key = f"post_detail_{post.id}"

        result = get_cached_post(post.id, queryset)

        assert result.id == post.id
        assert cache.get(cache_key) is not None
        assert cache.get(cache_key).id == post.id

    def test_avoids_db_queries_on_cached_data(self, post_factory):
        """Повторный вызов берет данные из кеша и не делает SQL-запросов."""
        post = post_factory()
        queryset = Post.objects.all()

        # Первый вызов - запись в кеш
        get_cached_post(post.id, queryset)

        # Второй вызов - данные из кеша
        with CaptureQueriesContext(connection) as queries:
            get_cached_post(post.id, queryset)

        assert len(queries) == 0

    def test_returns_shallow_copy_protects_cache(self, post_factory):
        """Сервис возвращает копию, защищая in-memory кеш от изменений."""
        post = post_factory(title="Original title")
        queryset = Post.objects.all()

        # Изменение сохраненного python-объекта
        result1 = get_cached_post(post.id, queryset)
        result1.title = "Mutated title"

        # Новый запрос, кешированный объект не должен быть изменен
        result2 = get_cached_post(post.id, queryset)

        assert result2.title == "Original title"
        assert result1.title != result2.title


@pytest.mark.django_db
class TestGetCachedTags:

    def test_returns_tags_and_populates_cache(self):
        """Сервис возвращает список тегов и сохраняет его в кеш, сортировка по name."""
        LowercaseTag.objects.create(name="b_tag2")
        LowercaseTag.objects.create(name="a_tag1")

        cache_key = "all_tags_list"

        result = get_cached_tags()

        assert len(result) == 2
        assert result[0].name == "a_tag1"
        assert result[1].name == "b_tag2"

        cached_data = cache.get(cache_key)
        assert cached_data is not None
        assert len(cached_data) == 2

        new_tag = LowercaseTag.objects.create(name="test_tag")

        with CaptureQueriesContext(connection) as queries:
            cached_data_new = get_cached_tags()

        assert cached_data_new[0].name == "a_tag1"
        assert cached_data_new[1].name == "b_tag2"
        assert new_tag not in cached_data_new

        # Повторный вызов списка тегов не делает SQL-запросов.
        assert len(queries) == 0
