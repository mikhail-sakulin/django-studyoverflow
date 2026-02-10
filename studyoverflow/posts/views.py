import json
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.cache import cache
from django.db import models
from django.db.models import Count, Prefetch
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from posts.forms import CommentCreateForm, CommentUpdateForm, PostCreateForm, PostFilterForm
from posts.models import Comment, Post
from posts.services.infrastructure import (
    CommentGetMethodMixin,
    CommentSortMixin,
    ContextTagMixin,
    HTMXHandle404Mixin,
    HTMXMessageMixin,
    LikeAnnotationsMixin,
    LoginRequiredHTMXMixin,
    PostAnnotateQuerysetMixin,
    PostFilterSortMixin,
    PostTagMixin,
    SingleObjectCacheMixin,
)
from users.services.infrastructure import IsAuthorOrModeratorMixin


logger = logging.getLogger(__name__)


class PostListView(ContextTagMixin, PostFilterSortMixin, PostAnnotateQuerysetMixin, ListView):
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


class PostCreateView(PostTagMixin, LoginRequiredHTMXMixin, SuccessMessageMixin, CreateView):
    """
    Класс-представление для создания нового поста.
    """

    form_class = PostCreateForm
    template_name = "posts/post_create.html"
    success_url = reverse_lazy("posts:list")
    success_message = "Пост успешно создан!"

    def get_context_data(self, **kwargs):
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
    model = Post
    template_name = "posts/post_detail.html"
    context_object_name = "post"

    def get_object(self, queryset=None):
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
        context = super().get_context_data(**kwargs)
        # Пустая форма в шаблон для написания комментария
        context["comment_form"] = CommentCreateForm()
        return context


class PostUpdateView(
    LoginRequiredMixin,
    IsAuthorOrModeratorMixin,
    SingleObjectCacheMixin,
    PostTagMixin,
    SuccessMessageMixin,
    UpdateView,
):
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


class CommentListView(LikeAnnotationsMixin, CommentSortMixin, ListView):
    model = Comment
    template_name = "posts/comments/comment_list.html"
    context_object_name = "root_comments"

    def _get_post_object(self):
        if not hasattr(self, "_post_object"):
            post_pk = self.kwargs.get("post_pk")
            self._post_object = get_object_or_404(
                Post.objects.annotate(comments_count=Count("comments")), pk=post_pk
            )
        return self._post_object

    def get_queryset(self):
        post = self._get_post_object()

        child_queryset = self.annotate_queryset(
            Comment.objects.select_related(
                "author", "post", "reply_to", "reply_to__author"
            ).order_by("-time_create")
        )

        queryset = (
            post.comments.roots()
            .select_related("author", "post")
            # prefetch_related для обратного доступа ForeignKey через related_name
            .prefetch_related(Prefetch("child_comments", queryset=child_queryset))
            .order_by("-time_create")
        )

        queryset = self.annotate_queryset(queryset)

        queryset = self.sort_comments(queryset)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self._get_post_object()
        context["post"] = post
        context["comment_form"] = CommentCreateForm()
        return context


class CommentRootCreateView(
    LoginRequiredHTMXMixin, HTMXMessageMixin, CommentGetMethodMixin, CreateView
):
    model = Comment
    form_class = CommentCreateForm
    template_name = "posts/comments/_comment_root_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        if not hasattr(self, "_cached_post"):
            self._cached_post = get_object_or_404(Post, id=self.kwargs.get("post_pk"))
        kwargs["post"] = self._cached_post
        return kwargs

    def get_context_data(self, form, form_valid=True, **kwargs):
        context = super().get_context_data(**kwargs)
        context.pop("form")
        reply_to = form.cleaned_data.get("reply_to")
        context = {
            "post": form.post,
            "comment": reply_to,
            "comment_form": self.form_class() if form_valid else form,
        }
        return context

    def form_valid(self, form):
        form.instance.post = form.post
        form.instance.author = self.request.user
        self.object = form.save()

        context = self.get_context_data(form, form_valid=True)

        logger.info(
            f"Создан комментарий (id: {self.object.id}) к посту (id: {form.post.id}).",
            extra={
                "comment_id": self.object.id,
                "post_id": form.post.id,
                "author_id": self.request.user.id,
                "event_type": "comment_create",
            },
        )

        response = render(self.request, self.template_name, context)
        response["HX-Trigger"] = json.dumps({"commentsUpdated": {}, "commentRootFormSuccess": {}})

        return self.htmx_message(
            message_text="Комментарий создан.", message_type="success", response=response
        )

    def form_invalid(self, form):
        context = self.get_context_data(form, form_valid=False)

        response = render(self.request, self.template_name, context)
        response["HX-Trigger"] = json.dumps({"commentRootFormError": {}})

        return response


class CommentChildCreateView(CommentRootCreateView):
    template_name = "posts/comments/_comment_child_form.html"

    def _add_errors_to_messages(self, form):
        messages.error(self.request, "Возможно, комментарий был удален.")
        for field, errors in form.errors.items():
            for error in errors:
                if field == "__all__":
                    # ошибки на уровне формы
                    messages.error(self.request, f"Ошибка: {error}")
                else:
                    # ошибки конкретного поля
                    messages.error(self.request, f'Ошибка в "{form.fields[field].label}": {error}')

    def form_valid(self, form):
        response = super().form_valid(form)

        reply_to = form.cleaned_data.get("reply_to")

        # Определяется commentId для события
        comment_id = reply_to.id

        # Передаются данные в формате JSON для HX-Trigger
        response["HX-Trigger"] = json.dumps(
            {"commentsUpdated": {}, "commentChildFormSuccess": {"commentId": comment_id}}
        )

        return self.htmx_message(
            message_text="Комментарий создан.", message_type="success", response=response
        )

    def form_invalid(self, form):
        response = super().form_invalid(form)

        reply_to = form.cleaned_data.get("reply_to")

        if not reply_to:
            self._add_errors_to_messages(form)
            response["HX-Refresh"] = "true"
            return response

        comment_id = reply_to.id

        response["HX-Trigger"] = json.dumps({"commentChildFormError": {"commentId": comment_id}})

        return response


class CommentUpdateView(
    LoginRequiredHTMXMixin,
    HTMXMessageMixin,
    IsAuthorOrModeratorMixin,
    SingleObjectCacheMixin,
    LikeAnnotationsMixin,
    HTMXHandle404Mixin,
    CommentGetMethodMixin,
    UpdateView,
):
    model = Comment
    form_class = CommentUpdateForm
    pk_url_kwarg = "comment_pk"
    template_name = "posts/comments/_comment_card.html"
    permission_required = "posts.moderate_comment"

    def get_queryset(self):
        queryset = super().get_queryset().select_related("author", "post")
        queryset = self.annotate_queryset(queryset)
        return queryset

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(**kwargs)
        context.pop("form")
        context = {
            "comment_update_form": form,
            "comment_form": self.form_class(),
            "comment": self.object,
            "post": self.object.post,
        }
        return context

    def form_valid(self, form):
        self.object = form.save()
        context = self.get_context_data(form)

        logger.info(
            f"Комментарий обновлен (id: {self.object.id}) "
            f"пользователем {self.request.user.username}.",
            extra={
                "comment_id": self.object.id,
                "post_id": self.object.post.id,
                "user_id": self.request.user.id,
                "event_type": "comment_update",
            },
        )

        response = render(self.request, self.template_name, context)
        response["HX-Trigger"] = json.dumps({"commentUpdateSuccess": {"commentId": self.object.id}})

        return self.htmx_message(
            message_text="Комментарий изменен.", message_type="success", response=response
        )

    def form_invalid(self, form):
        context = self.get_context_data(form)

        response = render(self.request, self.template_name, context)
        response["HX-Trigger"] = json.dumps({"commentUpdateError": {"commentId": self.object.id}})
        return response


class CommentDeleteView(
    LoginRequiredHTMXMixin,
    HTMXMessageMixin,
    HTMXHandle404Mixin,
    IsAuthorOrModeratorMixin,
    SingleObjectCacheMixin,
    CommentGetMethodMixin,
    DeleteView,
):
    model = Comment
    pk_url_kwarg = "comment_pk"
    permission_required = "posts.moderate_comment"

    def form_valid(self, form):
        comment_id = self.object.id
        post_id = self.object.post.id
        self.object.delete()

        logger.info(
            f"Комментарий удален (id: {comment_id}).",
            extra={
                "comment_id": comment_id,
                "post_id": post_id,
                "user_id": self.request.user.id,
                "event_type": "comment_delete",
            },
        )

        response = HttpResponse()
        response["HX-Trigger"] = json.dumps({"commentsUpdated": {}})

        return self.htmx_message(
            message_text="Комментарий удален.", message_type="info", response=response
        )


class ToggleLikeBaseView(LoginRequiredHTMXMixin, HTMXMessageMixin, View):
    model: type[models.Model]
    pk_url_kwarg: str = "pk"

    def _get_toggle_like_url(self, liked_object):
        return reverse_lazy("home")

    def post(self, request, *args, **kwargs):
        try:
            liked_object = self.model.objects.get(pk=kwargs[self.pk_url_kwarg])
        except self.model.DoesNotExist:
            response = HttpResponse(status=404)
            response["HX-Trigger"] = json.dumps({"reloadPage": True})

            messages.error(self.request, "Ресурс был удален.")

            return response

        like, created = liked_object.likes.get_or_create(user=request.user)

        if not created:
            like.delete()
            message_text = "Лайк удален."
            message_type = "info"
        else:
            message_text = "Лайк добавлен."
            message_type = "success"

        event_type = "like_add" if created else "like_remove"

        logger.info(
            f"Лайк {event_type} для {self.model.__name__} (id: {liked_object.id}).",
            extra={
                "object_type": self.model.__name__.lower(),
                "object_id": liked_object.id,
                "user_id": request.user.id,
                "event_type": event_type,
            },
        )

        context = {
            "toggle_like_url": self._get_toggle_like_url(liked_object),
            "liked_object": liked_object,
            "likes_count": liked_object.likes.count(),
            "user_has_liked": created,
        }

        response = render(request, "posts/likes/_like-button.html", context)

        return self.htmx_message(
            message_text=message_text, message_type=message_type, response=response
        )


class ToggleLikePostView(ToggleLikeBaseView):
    model = Post
    pk_url_kwarg = "post_pk"

    def _get_toggle_like_url(self, post):
        return reverse_lazy(
            "posts:toggle_like_post", kwargs={"post_pk": post.pk, "post_slug": post.slug}
        )


class ToggleLikeCommentView(ToggleLikeBaseView):
    model = Comment
    pk_url_kwarg = "comment_pk"

    def _get_toggle_like_url(self, comment):
        return reverse_lazy(
            "posts:toggle_like_comment",
            kwargs={
                "post_pk": comment.post.pk,
                "post_slug": comment.post.slug,
                "comment_pk": comment.pk,
            },
        )
