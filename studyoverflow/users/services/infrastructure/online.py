import logging

from django.core.cache import cache
from django.core.files.storage import storages
from django_redis import get_redis_connection


logger = logging.getLogger(__name__)


storage_default = storages["default"]


REDIS_KEY_PREFIX = "online_user"
ONLINE_SET_KEY = "online_users_set"
ONLINE_TTL = 120


def get_user_key_for_redis(user_id: int) -> str:
    return f"{REDIS_KEY_PREFIX}:{user_id}"


def set_user_online(user_id: int):
    """
    Помечает пользователя как онлайн.
    Создает временный user_key и добавляет ID в общее множество.
    """
    redis_conn = get_redis_connection("default")
    user_key = get_user_key_for_redis(user_id)

    with redis_conn.pipeline() as pipe:
        # Создание временного ключа user_key
        pipe.set(user_key, "1", ex=ONLINE_TTL)
        # Добавление ID пользователя во множество (set)
        pipe.sadd(ONLINE_SET_KEY, user_id)
        pipe.execute()


def is_user_online(user_id: int) -> bool:
    """
    Быстрая проверка статуса конкретного пользователя.
    """
    redis_conn = get_redis_connection("default")
    user_key = get_user_key_for_redis(user_id)
    return redis_conn.exists(user_key) == 1


def remove_user_offline(user_id: int):
    """
    Удаляет пользователя из онлайн.
    """
    redis_conn = get_redis_connection("default")
    user_key = get_user_key_for_redis(user_id)
    with redis_conn.pipeline() as pipe:
        pipe.delete(user_key)
        pipe.srem(ONLINE_SET_KEY, user_id)
        pipe.execute()


def get_online_user_ids() -> list:
    """
    Возвращает список ID всех пользователей онлайн и чистит устаревшие записи.
    """
    redis_conn = get_redis_connection("default")

    all_ids = [int(el) for el in redis_conn.smembers(ONLINE_SET_KEY)]
    if not all_ids:
        return []

    with redis_conn.pipeline() as pipe:
        for u_id in all_ids:
            pipe.exists(f"{get_user_key_for_redis(u_id)}")
        result = pipe.execute()

    active_ids = []
    expired_ids = []

    for u_id, exists in zip(all_ids, result):
        if exists:
            active_ids.append(u_id)
        else:
            expired_ids.append(u_id)

    if expired_ids:
        redis_conn.srem(ONLINE_SET_KEY, *expired_ids)

    return active_ids


def get_cached_online_user_ids() -> list:
    """
    Возвращает список ID всех пользователей онлайн из кеша.
    """
    cache_key = "cached_online_users_set"
    data = cache.get(cache_key)

    if data is None:
        data = get_online_user_ids()
        # кеш 2 сек, чтобы данные быстро обновлялись для наглядности
        cache.set(cache_key, data, timeout=2)

    return data
