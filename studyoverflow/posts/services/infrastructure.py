"""
Модуль содержит инфраструктурную логику приложения posts.
"""

from typing import Generic, Protocol, TypeVar

from posts.models import LowercaseTag


class PostTagMixinProtocol(Protocol):
    """
    Protocol для миксина, который ожидает реализацию указанных методов в MRO.
    """

    def form_valid(self, form): ...
    def get_context_data(self, **kwargs): ...


# Любой класс типа T_Parent обязан соответствовать протоколу PostTagMixinProtocol
T_Parent = TypeVar("T_Parent", bound=PostTagMixinProtocol)


class PostTagMixin(Generic[T_Parent]):
    """
    Миксин для работы с тегами в формах PostCreate/PostUpdate.
    Добавляет обработку тегов при сохранении и список всех тегов в контекст.

    Миксин ожидает, что его MRO содержит класс, являющийся типом T_Parent.
    """

    def form_valid(self: T_Parent, form):
        # Сохраняется объект post и возвращается response
        response = super().form_valid(form)  # type: ignore
        post = form.instance
        tags = form.cleaned_data.get("tags")
        if tags is not None:
            # Обновление связи ManyToMany: сопоставление указанных тегов с постом
            post.tags.set(tags)
        return response

    def get_context_data(self: T_Parent, **kwargs):
        context = super().get_context_data(**kwargs)  # type: ignore
        context["all_tags"] = LowercaseTag.objects.all().order_by("name")
        return context
