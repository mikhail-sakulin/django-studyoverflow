"""
Некоторые миксины для классов-представлений.
"""

from typing import Any

from django.core.cache import cache
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect
from posts.models import LowercaseTag, Post


class ContextTagMixin:
    """
    Миксин для добавления полного списка тегов в контекст шаблона.
    """

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


class PostAuthorMixin:
    """
    Миксин для автоматического назначения автора при сохранении формы поста.
    """

    request: HttpRequest

    def form_valid(self, form):
        """
        Устанавливает автора для нового поста перед сохранением в БД.
        """
        post_creating = form.instance.pk is None

        if post_creating and self.request.user.is_authenticated:
            form.instance.author = self.request.user

        return super().form_valid(form)  # type: ignore


class CommentGetMethodMixin:
    """
    Миксин для перенаправления GET-запросов с комментариев на страницу поста.
    """

    kwargs: dict[str, Any]

    def get(self, request, *args, **kwargs):
        post_id = self.kwargs.get("post_pk")
        post = get_object_or_404(Post, id=post_id)
        return redirect("posts:detail", pk=post.pk, slug=post.slug)


class SingleObjectCacheMixin:
    """
    Миксин для кеширования объекта в рамках одного запроса.
    """

    def get_object(self, queryset=None):
        if not hasattr(self, "object") or self.object is None:  # type: ignore[has-type]
            self.object = super().get_object(queryset)  # type: ignore[misc]
        return self.object
