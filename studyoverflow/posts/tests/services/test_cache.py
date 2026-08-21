import pytest
from django.core.cache import cache
from django.db import connection
from django.http import Http404
from django.test.utils import CaptureQueriesContext

from posts.models import LowercaseTag, Post
from posts.services import (
    delete_cache_post_detail,
    delete_cache_tags_list,
    delete_cached_posts_by_author,
    get_cached_post,
    get_cached_tags,
    get_post_cache_key,
    get_tags_cache_key,
)


@pytest.fixture(autouse=True)
def clear_cache():
    """Очищает кеш до и после каждого теста."""
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
class TestPostCacheKey:

    def test_returns_expected_key(self):
        """Возвращает корректный ключ кеша поста."""
        assert get_post_cache_key(5) == "post_detail_5"


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

        cache_key = get_post_cache_key(post.id)

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
class TestDeleteCachedPostsByAuthor:

    def test_deletes_cache_of_all_posts_for_author(self, user_factory, post_factory):
        """Удаляет кеш всех постов указанного автора, оставляя кеш постов других авторов."""
        author1 = user_factory()
        author2 = user_factory()

        post1_author1 = post_factory(author=author1)
        post2_author1 = post_factory(author=author1)

        post_author2 = post_factory(author=author2)

        # Кеширование постов автора author1
        queryset = Post.objects.all()
        get_cached_post(post1_author1.id, queryset)
        get_cached_post(post2_author1.id, queryset)
        get_cached_post(post_author2.id, queryset)

        # Проверка, что кеш существует
        key1_post_author1 = get_post_cache_key(post1_author1.id)
        key2_post_author2 = get_post_cache_key(post2_author1.id)
        key_post_author2 = get_post_cache_key(post_author2.id)
        assert cache.get(key1_post_author1) is not None
        assert cache.get(key2_post_author2) is not None
        assert cache.get(key_post_author2) is not None

        # Удаление кеша постов author1
        delete_cached_posts_by_author(author1.id)

        # Кеш постов автора author1 должен быть пуст, а кеш постов author2 должен существовать
        assert cache.get(key1_post_author1) is None
        assert cache.get(key2_post_author2) is None
        assert cache.get(key_post_author2) is not None

    def test_does_nothing_for_author_without_posts(self, user_factory):
        """Если у автора нет постов, сервис не вызывает исключений."""
        author = user_factory()
        delete_cached_posts_by_author(author.id)

    def test_works_with_empty_cache(self, user_factory, post_factory):
        """Если кеш постов уже пуст, сервис не вызывает исключений."""
        author = user_factory()
        post = post_factory(author=author)

        delete_cached_posts_by_author(author.id)

        key = get_post_cache_key(post.id)
        assert cache.get(key) is None

        # Вызов сервиса не вызывает исключений
        delete_cached_posts_by_author(author.id)


@pytest.mark.django_db
class TestDeleteCachePostDetail:

    def test_deletes_cache(self, post_factory):
        """Удаляет объект поста из кеша."""
        post = post_factory()
        queryset = Post.objects.all()

        get_cached_post(post.id, queryset)

        cache_key = get_post_cache_key(post.id)
        assert cache.get(cache_key) is not None

        delete_cache_post_detail(post.id)

        assert cache.get(cache_key) is None


@pytest.mark.django_db
class TestGetTagsCacheKey:

    def test_returns_expected_key(self):
        """Возвращает корректный ключ кеша списка тегов."""
        assert get_tags_cache_key() == "all_tags_list"


@pytest.mark.django_db
class TestGetCachedTags:

    def test_returns_tags_and_populates_cache(self):
        """Сервис возвращает список тегов и сохраняет его в кеш, сортировка по name."""
        LowercaseTag.objects.create(name="b_tag2")
        LowercaseTag.objects.create(name="a_tag1")

        cache_key = get_tags_cache_key()

        result = get_cached_tags()

        assert len(result) == 2
        assert result[0].name == "a_tag1"
        assert result[1].name == "b_tag2"

        cached_data = cache.get(cache_key)
        assert cached_data is not None
        assert len(cached_data) == 2

        with CaptureQueriesContext(connection) as queries:
            cached_data = get_cached_tags()

        assert cached_data[0].name == "a_tag1"
        assert cached_data[1].name == "b_tag2"

        # Повторный вызов списка тегов не делает SQL-запросов.
        assert len(queries) == 0


@pytest.mark.django_db
class TestDeleteCacheTagsList:

    def test_deletes_cache(self):
        """Удаляет кеш списка тегов из хранилища."""
        LowercaseTag.objects.create(name="python")
        get_cached_tags()

        cache_key = get_tags_cache_key()
        assert cache.get(cache_key) is not None

        delete_cache_tags_list()

        assert cache.get(cache_key) is None
