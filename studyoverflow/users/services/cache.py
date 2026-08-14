import copy

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.shortcuts import get_object_or_404


def get_user_cache_key(username: str) -> str:
    """Возвращает ключ кэша для объекта пользователя."""
    return f"user_profile_{username.lower()}"


def get_cached_user(username: str):
    """
    Возвращает кешированный объект пользователя по username.

    Используется в Web и API представлениях.
    """
    user_model = get_user_model()

    cache_key = get_user_cache_key(username)

    user = cache.get(cache_key)

    if user is None:
        user = get_object_or_404(user_model, username=username)
        # Кеш 10 минут
        cache.set(cache_key, user, timeout=10 * 60)

    # Возвращается поверхностная копия, чтобы изменения объекта в коде
    # не изменили объект в кеше при тестах, когда кеш в оперативной памяти.
    #
    # По умолчанию в "django.core.cache.backends.locmem.LocMemCache" объекты сериализуются
    # через pickle, поэтому сохраняются копии и изменение python-объектов не изменит
    # захешированные объекты, но copy все равно используется для надежности и наглядности.
    return copy.copy(user)


def delete_cache_user(username: str) -> None:
    """Удаляет кэш объекта пользователя по username."""
    cache_key = get_user_cache_key(username)
    cache.delete(cache_key)
