import copy

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.shortcuts import get_object_or_404


def get_cached_user_profile(username: str):
    """
    Возвращает кешированный объект профиля пользователя по username.

    Используется в Web и API представлениях.
    """
    user_model = get_user_model()

    cache_key = f"user_profile_{username}"

    user = cache.get(cache_key)

    if user is None:
        user = get_object_or_404(user_model, username=username)
        # кеш 2 сек, чтобы данные быстро обновлялись для наглядности
        cache.set(cache_key, user, timeout=2)

    # Возвращается поверхностная копия, чтобы изменения объекта в коде
    # не изменили объект в кеше при тестах, когда кеш в оперативной памяти.
    #
    # По умолчанию в "django.core.cache.backends.locmem.LocMemCache" объекты сериализуются
    # через pickle, поэтому сохраняются копии и изменение python-объектов не изменит
    # захешируемые объекты, но copy все равно используется для надежности и наглядности.
    return copy.copy(user)
