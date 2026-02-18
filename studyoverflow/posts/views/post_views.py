import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.cache import cache
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from posts.forms import CommentCreateForm, PostCreateForm, PostFilterForm
from posts.models import Post
from users.views.mixins import IsAuthorOrModeratorMixin

from .mixins import (
    ContextTagMixin,
    LoginRequiredHTMXMixin,
    PostAnnotateQuerysetMixin,
    PostAuthorMixin,
    PostFilterSortMixin,
    SingleObjectCacheMixin,
)


logger = logging.getLogger(__name__)


class PostListView(ContextTagMixin, PostFilterSortMixin, PostAnnotateQuerysetMixin, ListView):
    """
    Страница со списком постов с тегами, аннотациями, фильтрацией и сортировкой.

    Использует:
    - ContextTagMixin: для добавления тегов в контекст.
    - PostAnnotateQuerysetMixin: select_related, prefetch_related и аннотации.
    - PostFilterSortMixin: фильтрация и сортировка.
    """

    model = Post
    template_name = "posts/post_list.html"
    context_object_name = "posts"
    paginate_by = 7
    extra_context = {"section_of_menu_selected": "posts:list"}

    def get_queryset(self):
        queryset = super().get_queryset()

        # Фильтрация по полям модели (через PostFilterSortMixin)
        queryset = self.filter_by_model_fields(queryset, self.request)

        # select_related, prefetch_related и аннотации (через PostAnnotateQuerysetMixin)
        queryset = self.get_annotate_queryset(queryset)

        # Фильтрация и сортировка по аннотированным полям (через PostFilterSortMixin)
        queryset = self.filter_and_sort_by_annotations(queryset, self.request)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        filter_form = PostFilterForm(self.request.GET or None)

        if filter_form.data.get("author"):
            filter_form.is_valid()

        context["filter_form"] = filter_form

        get_params = self.request.GET.copy()
        if "page" in get_params:
            get_params.pop("page")
        context["querystring"] = get_params.urlencode()

        return context


class PostCreateView(PostAuthorMixin, LoginRequiredHTMXMixin, SuccessMessageMixin, CreateView):
    """
    Страница создания нового поста.

    Логирует создание поста и добавляет сообщение об успешном создании.
    """

    form_class = PostCreateForm
    template_name = "posts/post_create.html"
    success_url = reverse_lazy("posts:list")
    success_message = "Пост успешно создан!"

    def get_context_data(self, **kwargs):
        """Добавляет выбранный раздел меню в контекст."""
        context = super().get_context_data(**kwargs)
        context["section_of_menu_selected"] = "posts:create"
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        post = self.object
        logger.info(
            f"Пост создан: {post.title} (id: {post.id}).",
            extra={
                "post_id": post.id,
                "author_id": self.request.user.id,
                "event_type": "post_create",
            },
        )
        return response


class PostDetailView(PostAnnotateQuerysetMixin, DetailView):
    """
    Страница просмотра подробностей поста с кешированием его данных.
    """

    model = Post
    template_name = "posts/post_detail.html"
    context_object_name = "post"

    def get_object(self, queryset=None):
        """Возвращает объект поста с кешированием."""
        post_id = self.kwargs.get(self.pk_url_kwarg)
        user_id = self.request.user.id if self.request.user.is_authenticated else "anon"
        cache_key = f"post_detail_{post_id}_u{user_id}"

        obj = cache.get(cache_key)
        if not obj:
            obj = super().get_object(queryset)
            # кеш 2 сек, чтобы данные быстро обновлялись для наглядности
            cache.set(cache_key, obj, 2)
        return obj

    def get_queryset(self):
        queryset = super().get_queryset()

        # select_related, prefetch_related и аннотации (через PostAnnotateQuerysetMixin)
        return super().get_annotate_queryset(queryset)

    def get_context_data(self, **kwargs):
        """Добавляет пустую форму для создания комментария в контекст."""
        context = super().get_context_data(**kwargs)
        # Пустая форма в шаблон для написания комментария
        context["comment_form"] = CommentCreateForm()
        return context


class PostUpdateView(
    LoginRequiredMixin,
    IsAuthorOrModeratorMixin,
    SingleObjectCacheMixin,
    SuccessMessageMixin,
    UpdateView,
):
    """
    Страница редактирования поста.

    Логирует изменения и проверяет права пользователя.
    """

    model = Post
    form_class = PostCreateForm
    template_name = "posts/post_edit.html"
    context_object_name = "post"
    permission_required = "posts.moderate_post"
    success_message = "Пост успешно изменен!"

    def get_queryset(self):
        return super().get_queryset().select_related("author").prefetch_related("tags")

    def form_valid(self, form):
        response = super().form_valid(form)
        post = self.object
        logger.info(
            f"Пост отредактирован: {post.title} (id: {post.id}).",
            extra={
                "post_id": post.id,
                "editor_id": self.request.user.id,
                "event_type": "post_update",
            },
        )
        return response


class PostDeleteView(
    LoginRequiredMixin, IsAuthorOrModeratorMixin, SingleObjectCacheMixin, DeleteView
):
    """
    Удаление поста.

    Логирует удаление и показывает сообщение пользователю.
    """

    model = Post
    success_url = reverse_lazy("posts:list")
    permission_required = "posts.moderate_post"

    def form_valid(self, form):
        post = self.get_object()
        logger.info(
            f"Пост удален: {post.title} (id: {post.id}).",
            extra={
                "post_id": post.id,
                "deleter_id": self.request.user.id,
                "event_type": "post_delete",
            },
        )

        messages.info(self.request, "Пост удален.")
        return super().form_valid(form)
