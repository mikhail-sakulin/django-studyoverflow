import pytest
from django.core.cache import cache
from django.db import connection
from django.http import Http404
from django.test.utils import CaptureQueriesContext

from users.services import delete_cache_user, get_cached_user, get_user_cache_key


@pytest.fixture(autouse=True)
def clear_cache():
    """Очищает кеш до и после каждого теста."""
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
class TestUserProfileCacheKey:

    def test_returns_expected_key(self):
        """Возвращает корректный ключ кеша объекта пользователя в нижнем регистре."""
        assert get_user_cache_key("TestUser") == "user_profile_testuser"


@pytest.mark.django_db
class TestGetCachedUserProfile:
    def test_raises_404_for_nonexistent_user(self):
        """Если пользователя не существует, вызывается 404."""
        with pytest.raises(Http404):
            get_cached_user("non_existent_ghost")

    def test_returns_user_and_populates_cache(self, user_factory):
        """Функция возвращает пользователя и сохраняет его в кеш."""
        user = user_factory(username="test_user")
        cache_key = get_user_cache_key(user.username)

        result = get_cached_user(user.username)

        assert result.username == user.username
        assert cache.get(cache_key) is not None
        assert cache.get(cache_key).username == user.username

    def test_avoids_db_queries_on_cached_data(self, user_factory):
        """Повторный вызов берет данные из кеша и не делает SQL-запросов."""
        user = user_factory(username="cached_user")

        # Первый вызов - обращение к БД и запись в кеш
        get_cached_user(user.username)

        # Второй вызов - данные берется из кеша
        with CaptureQueriesContext(connection) as queries:
            get_cached_user(user.username)

        # Запросов к БД не было во втором запросе
        assert len(queries) == 0

    def test_returns_shallow_copy_protects_cache(self, user_factory):
        """Сервис возвращает копию, защищая in-memory кеш от изменений."""
        user = user_factory(username="copy_user")

        # Кешированный объект изменяется
        result1 = get_cached_user(user.username)
        result1.username = "mutated_username"

        # Новый запрос, кешированный объект не должен изменяться
        result2 = get_cached_user(user.username)

        assert result2.username == "copy_user"
        assert result1.username != result2.username


@pytest.mark.django_db
class TestDeleteCacheUserProfile:

    def test_deletes_cache(self, user_factory):
        """Удаляет объект пользователя из кеша."""
        user = user_factory()

        get_cached_user(user.username)

        cache_key = get_user_cache_key(user.username)
        assert cache.get(cache_key) is not None

        delete_cache_user(user.username)

        assert cache.get(cache_key) is None
