"""
Модуль содержит инфраструктурную логику приложения posts.
"""

import json
from typing import Any, Generic, Optional, Protocol, TypeVar

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db.models import Count, Exists, OuterRef, Q
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from posts.models import Like, LowercaseTag, Post
from posts.services.domain import normalize_tag_name


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

        # Сохраняется объект post и возвращается response
        response = super().form_valid(form)  # type: ignore

        tags = form.cleaned_data.get("tags")
        if tags is not None:
            # Обновление связи ManyToMany: сопоставление указанных тегов с постом
            form.instance.tags.set([normalize_tag_name(tag) for tag in tags])

        return response


class LikeAnnotationsMixin:
    like_model = None
    like_related_field = "likes"
    request: HttpRequest

    def _get_content_type(self, model):
        return ContentType.objects.get_for_model(model)

    def annotate_queryset(self, queryset):
        if "likes_count" not in queryset.query.annotations:
            queryset = queryset.annotate(likes_count=Count(self.like_related_field))

        user = getattr(self.request, "user", None)

        if user and user.is_authenticated:
            content_type = self._get_content_type(queryset.model)

            queryset = queryset.annotate(
                user_has_liked=Exists(
                    Like.objects.filter(
                        content_type=content_type, object_id=OuterRef("pk"), user=user
                    )
                )
            )
        else:
            queryset = queryset.annotate(user_has_liked=Exists(Like.objects.none()))

        return queryset

    def annotate_object(self, obj):
        queryset = self.annotate_queryset(obj.__class__.objects.filter(pk=obj.pk))
        annotated = queryset.first()

        obj.likes_count = annotated.likes_count
        obj.user_has_liked = annotated.user_has_liked

        return obj


class PostAnnotateQuerysetMixin(LikeAnnotationsMixin):
    """
    Аннотированный queryset для постов:
    - select_related author
    - prefetch_related tags
    - annotate likes_count и comments_count
    """

    model: type[Post]

    def get_annotate_queryset(self, queryset):  # type: ignore
        queryset = (
            queryset.select_related("author")
            .prefetch_related("tags")
            .annotate(
                likes_count=Count("likes", distinct=True),
                comments_count=Count("comments", distinct=True),
            )
        )
        queryset = super().annotate_queryset(queryset)
        return queryset


class PostFilterSortMixin:
    """
    Миксин для фильтрации и сортировки постов по GET-параметрам:
        - q: поиск по заголовку или содержимому
        - tags: теги через запятую
        - tag_match: any/all
        - author: имя автора
        - has_comments: yes/no
        - sort: created/likes/answers
        - order: asc/desc
    """

    def filter_by_model_fields(self, queryset, request):
        """
        Фильтрация по полям модели (q, tags, author).
        """

        # Поиск по тексту
        q = request.GET.get("q", "").strip()
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) | Q(content__icontains=q) | Q(tags__name__icontains=q)
            ).distinct()

        # Фильтр по тегам
        tags = request.GET.get("tags", "").strip()
        tag_match = request.GET.get("tag_match", "any")
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
            if tag_list:
                if tag_match == "any":
                    queryset = queryset.filter(tags__name__in=tag_list)
                else:
                    for tag_name in tag_list:
                        queryset = queryset.filter(tags__name=tag_name)
                queryset = queryset.distinct()

        # Фильтр по автору
        author = request.GET.get("author", "").strip()
        if author:
            queryset = queryset.filter(author__username__iexact=author)

        return queryset

    def filter_and_sort_by_annotations(self, queryset, request):
        """
        Фильтрация и сортировка по аннотациям (likes_count, comments_count).
        """

        # Фильтр по наличию комментариев
        has_comments = request.GET.get("has_comments", "any")
        if has_comments == "yes":
            queryset = queryset.filter(comments_count__gt=0)
        elif has_comments == "no":
            queryset = queryset.filter(comments_count=0)

        ordering_map = {
            "created": "time_create",
            "likes": "likes_count",
            "comments": "comments_count",
        }

        # Сортировка
        sort = request.GET.get("sort")
        sort = sort if sort in ordering_map else "created"

        order = request.GET.get("order")
        order = order if order in ("asc", "desc") else "desc"

        ordering_field = ordering_map.get(sort, "time_create")

        if order == "desc":
            ordering_field = f"-{ordering_field}"

        queryset = queryset.order_by(ordering_field, "-time_create")

        return queryset


class CommentGetMethodMixin:
    kwargs: dict[str, Any]

    def get(self, request, *args, **kwargs):
        post_id = self.kwargs.get("post_pk")
        post = get_object_or_404(Post, id=post_id)
        return redirect("posts:detail", pk=post.pk, slug=post.slug)


class HTMXMessageMixin:
    def htmx_message(
        self,
        *,
        message_text: str,
        message_type: str = "success",
        response: Optional[HttpResponse] = None,
        reswap_none: bool = False,
    ) -> HttpResponse:
        response = response or HttpResponse()

        if reswap_none:
            response["HX-Reswap"] = "none"

        # текущий header
        hx_trigger = response.get("HX-Trigger")

        # десериализация, если есть данные, иначе пустой словарь
        if hx_trigger:
            try:
                hx_data = json.loads(hx_trigger)
            except json.JSONDecodeError:
                hx_data = {}
        else:
            hx_data = {}

        # новое событие showMessage
        hx_data["showMessage"] = {
            "text": message_text,
            "type": message_type,
        }

        # сохранение обратно в response
        response["HX-Trigger"] = json.dumps(hx_data)

        return response


class LoginRequiredHTMXMixin(LoginRequiredMixin, HTMXMessageMixin):
    message_text = "Сначала войдите в аккаунт."
    message_type = "info"

    def dispatch(self, request, *args, **kwargs):
        if request.headers.get("Hx-Request") and not request.user.is_authenticated:
            return self.htmx_message(
                message_text=self.message_text,
                message_type=self.message_type,
                reswap_none=True,
            )

        return super().dispatch(request, *args, **kwargs)


class LoginRequiredRedirectHTMXMixin(LoginRequiredMixin):
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
                response = HttpResponse()
                response["HX-Trigger"] = json.dumps({"commentsUpdated": {}})
                return response
            raise
