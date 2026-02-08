from typing import Generic, Protocol, TypeVar

from django.core.cache import cache
from django.http import HttpRequest
from posts.models import LowercaseTag


class PostTagMixinProtocol(Protocol):
    """
    Protocol для миксина, который ожидает реализацию указанных методов в MRO.
    """

    request: HttpRequest

    def form_valid(self, form):
        pass

    def get_context_data(self, **kwargs):
        pass


# Любой класс типа T_Parent обязан соответствовать протоколу PostTagMixinProtocol
T_Parent = TypeVar("T_Parent", bound=PostTagMixinProtocol)


class ContextTagMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)  # type: ignore

        cache_key = "all_tags_list"

        tags = cache.get(cache_key)
        if tags is None:
            tags = list(LowercaseTag.objects.all().order_by("name").values_list("name", flat=True))
            # кеш 2 сек, чтобы данные быстро обновлялись для наглядности
            cache.set(cache_key, tags, 2)

        context["all_tags"] = tags
        return context


class PostTagMixin(ContextTagMixin, Generic[T_Parent]):
    """
    Миксин для работы с тегами в формах PostCreate/PostUpdate.
    Добавляет обработку тегов при сохранении и список всех тегов в контекст.

    Миксин ожидает, что его MRO содержит класс, являющийся типом T_Parent.
    """

    def form_valid(self: T_Parent, form):
        post_creating = form.instance.pk is None

        if post_creating and self.request.user.is_authenticated:
            form.instance.author = self.request.user

        return super().form_valid(form)  # type: ignore[misc]
