from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from django.core.cache import cache
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404


if TYPE_CHECKING:
    from posts.models import Post


def get_post_cache_key(post_id: int) -> str:
    """Возвращает ключ для кеширования конкретного поста."""
    return f"post_detail_{post_id}"


def get_cached_post(post_id: int, queryset: QuerySet[Post]):
    """
    Возвращает кешированный объект поста.

    Используется в Web и API представлениях.

    Кешируется только общая информация поста без пользовательских данных,
    например без флага о статусе лайка от пользователя.
    """

    cache_key = get_post_cache_key(post_id)

    post = cache.get(cache_key)

    if post is None:
        post = get_object_or_404(queryset, pk=post_id)
        # кеш 2 сек, чтобы данные быстро обновлялись для наглядности
        cache.set(cache_key, post, timeout=2)

    # Поверхностная копия объекта, чтобы изменение флага лайка от пользователя
    # не затронула объект внутри кеша при тестировании в оперативной памяти.
    #
    # Стандартный кеш Django в оперативной памяти LocMemCache не хранит прямые ссылки на
    # объекты Python, объекты сериализуются через pickle, но copy используется для надежности и
    # наглядности.
    return copy.copy(post)


def delete_cache_post_detail(post_id: int):
    """Удаляет кеш поста."""
    cache_key = get_post_cache_key(post_id)
    cache.delete(cache_key)


def get_tags_cache_key() -> str:
    """Возвращает ключ для кеширования списка тегов."""
    return "all_tags_list"


def get_cached_tags():
    """
    Возвращает кешированный список всех тегов.

    Используется в Web и API представлениях.
    """
    # Локальный импорт для избежания циклических импортов
    from posts.models import LowercaseTag

    cache_key = get_tags_cache_key()

    tags = cache.get(cache_key)

    if tags is None:
        tags = list(LowercaseTag.objects.order_by("name"))
        # кеш 2 сек, чтобы данные быстро обновлялись для наглядности
        cache.set(cache_key, tags, timeout=2)

    return tags


def delete_cache_tags_list():
    """Удаляет кеш списка всех тегов."""
    cache_key = get_tags_cache_key()
    cache.delete(cache_key)
