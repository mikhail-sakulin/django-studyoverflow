import fakeredis
import pytest
from django.core.cache import cache

from users.services.online import (
    ONLINE_SET_KEY,
    ONLINE_TTL,
    REDIS_KEY_PREFIX,
    async_set_user_online,
    get_cached_online_user_ids,
    get_online_user_ids,
    get_user_key_for_redis,
    is_user_online,
    remove_user_offline,
    set_user_online,
)


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def fake_async_redis(mocker):
    """
    Подменяет асинхронный клиент Redis через fakeredis и возвращает его.

    Это Fake подмена (полноценная рабочая реализация) через Python-объект.

    Фикстура для замены синхронного клиента Redis задается в conftest.py корня Django-проекта.
    """
    client = fakeredis.FakeAsyncRedis(server=fakeredis.FakeServer())
    mocker.patch("users.services.online.get_async_redis", return_value=client)
    return client


@pytest.fixture(autouse=True)
def reset_async_redis_singleton():
    """
    Сбрасывает синглтон асинхронного Redis-клиента после каждого теста.

    Фикстура задается для сброса состояния в случае использования реального
    асинхронного Redis-клиента в тестах.
    """
    import users.services.online as online_module

    online_module._async_redis_client = None
    yield
    online_module._async_redis_client = None


def test_get_user_key_for_redis():
    """Проверяет правильность формирования Redis-ключа."""
    user_id = 5
    key = get_user_key_for_redis(user_id)
    assert key == f"{REDIS_KEY_PREFIX}:{user_id}"


def test_set_user_online(fake_redis):
    """Проверяет отправку данных в Redis при установке онлайн-статуса."""
    set_user_online(5)

    key = get_user_key_for_redis(5)
    assert fake_redis.exists(key) == 1
    assert 0 < fake_redis.ttl(key) <= ONLINE_TTL
    assert fake_redis.sismember(ONLINE_SET_KEY, 5)


@pytest.mark.asyncio
async def test_async_set_user_online(fake_async_redis):
    """Проверяет асинхронную отправку данных в Redis при установке онлайн-статуса."""
    await async_set_user_online(5)

    key = get_user_key_for_redis(5)
    ttl = await fake_async_redis.ttl(key)
    assert await fake_async_redis.exists(key) == 1
    assert 0 < ttl <= ONLINE_TTL
    assert await fake_async_redis.sismember(ONLINE_SET_KEY, str(5))


def test_is_user_online(fake_redis):
    """Проверяет онлайн- и офлайн-статус пользователя."""
    assert is_user_online(5) is False
    set_user_online(5)
    assert is_user_online(5) is True


def test_remove_user_offline(fake_redis):
    """Проверяет удаление ключа из Redis при уходе пользователя в офлайн."""
    set_user_online(5)

    remove_user_offline(5)

    assert is_user_online(5) is False
    assert not fake_redis.sismember(ONLINE_SET_KEY, str(5))


class TestGetOnlineUserIds:
    def test_get_online_user_ids_no_users(self, fake_redis):
        """Если пользователей онлайн не, то множество онлайн-пользователей пусто."""
        assert get_online_user_ids() == []

    def test_get_online_user_ids_filters_expired(self, fake_redis):
        """Проверяет фильтрацию и удаление просроченных сессий пользователей."""
        set_user_online(10)
        set_user_online(20)
        # TTL-ключ пользователя 20 истек, а id остался во множестве
        fake_redis.delete(get_user_key_for_redis(20))

        assert get_online_user_ids() == [10]
        assert {int(i) for i in fake_redis.smembers(ONLINE_SET_KEY)} == {10}

    def test_get_online_user_ids_no_expired(self):
        """Если просроченных записей во множестве нет — возвращаются все."""
        set_user_online(10)
        set_user_online(20)

        assert sorted(get_online_user_ids()) == [10, 20]


def test_cached_online_user_ids_are_cached(fake_redis):
    """Проверяет кеширование множество онлайн-пользователей."""
    set_user_online(1)
    assert get_cached_online_user_ids() == [1]

    set_user_online(2)
    # Ответ из кеша, кеш не обновлялся
    assert get_cached_online_user_ids() == [1]

    cache.clear()
    # Кеш после обновления, данные обновлены
    assert sorted(get_cached_online_user_ids()) == [1, 2]
