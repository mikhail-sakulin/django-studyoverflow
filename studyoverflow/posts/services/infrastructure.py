"""
Модуль содержит инфраструктурную логику приложения posts.
"""

from typing import Any, Generic, Protocol, TypeVar

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Exists, OuterRef
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from posts.models import Like, LowercaseTag, Post


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


class PostQuerysetMixin:
    model: type[Post]
    request: HttpRequest

    def get_queryset(self):  # type: ignore
        queryset = (
            self.model.objects.all()
            .select_related("author")
            .prefetch_related("tags", "likes")
            .annotate(likes_count=Count("likes"))
            .order_by("-time_create")
        )
        if self.request.user.is_authenticated:
            content_type = ContentType.objects.get_for_model(self.model)
            queryset = queryset.annotate(
                user_has_liked=Exists(
                    Like.objects.filter(
                        content_type=content_type, object_id=OuterRef("pk"), user=self.request.user
                    )
                )
            )
        return queryset


class CommentGetMethodMixin:
    kwargs: dict[str, Any]

    def get(self, request, *args, **kwargs):
        post_id = self.kwargs.get("post_pk")
        post = get_object_or_404(Post, id=post_id)
        return redirect("posts:detail", pk=post.pk, slug=post.slug)


class LoginRequiredHTMXMixin(LoginRequiredMixin):
    """
    Расширение LoginRequiredMixin, чтобы HTMX делал редирект на страницу логина.
    """

    def handle_no_permission(self):
        if self.request.headers.get("Hx-Request"):
            return HttpResponse(headers={"HX-Redirect": f"{self.get_login_url()}"})
        return super().handle_no_permission()


class HTMXHandle404Mixin:
    """
    Обрабатывает Http404 для HTMX-запросов, чтобы не выбрасывать ошибку,
    а триггерить обновление комментариев.
    """

    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)  # type: ignore
        except Http404:
            if request.headers.get("Hx-Request"):
                response = HttpResponse(headers={"HX-Trigger": "commentsUpdated"})
                return response
            raise
