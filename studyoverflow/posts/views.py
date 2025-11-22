import json

from django.contrib import messages
from django.db import models, transaction
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
    HTMXHandle404Mixin,
    LikeAnnotationsMixin,
    LoginRequiredHTMXMixin,
    PostAnnotateQuerysetMixin,
    PostFilterSortMixin,
    PostTagMixin,
)


class PostListView(PostTagMixin, PostFilterSortMixin, PostAnnotateQuerysetMixin, ListView):
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


class PostCreateView(PostTagMixin, LoginRequiredHTMXMixin, CreateView):
    """
    Класс-представление для создания нового поста.
    """

    form_class = PostCreateForm
    template_name = "posts/post_create.html"
    success_url = reverse_lazy("home")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["section_of_menu_selected"] = "posts:create"
        return context


class PostDetailView(PostAnnotateQuerysetMixin, DetailView):
    model = Post
    template_name = "posts/post_detail.html"
    context_object_name = "post"

    def get_queryset(self):
        queryset = super().get_queryset()

        # select_related, prefetch_related и аннотации (через PostAnnotateQuerysetMixin)
        return super().annotate_queryset(queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Пустая форма в шаблон для написания комментария
        context["comment_form"] = CommentCreateForm()
        return context


class PostUpdateView(LoginRequiredHTMXMixin, PostTagMixin, UpdateView):
    model = Post
    form_class = PostCreateForm
    template_name = "posts/post_edit.html"
    context_object_name = "post"


class CommentListView(LikeAnnotationsMixin, ListView):
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
            Comment.objects.select_related("author", "post").order_by("-time_create")
        )

        queryset = (
            post.comments.roots()
            .select_related("author", "post")
            .prefetch_related(Prefetch("child_comments", queryset=child_queryset))
            .order_by("-time_create")
        )

        queryset = self.annotate_queryset(queryset)

        ordering_map = {
            "date": "time_create",
            "likes": "likes_count",
        }

        sort = self.request.GET.get("comment_sort")
        sort = sort if sort in ordering_map else "date"

        order = self.request.GET.get("comment_order")
        order = order if order in ("asc", "desc") else "desc"

        field = ordering_map.get(sort, "time_create")
        if order == "desc":
            field = f"-{field}"

        queryset = queryset.order_by(field, "-time_create")

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self._get_post_object()
        context["post"] = post
        context["comment_form"] = CommentCreateForm()
        return context


class CommentRootCreateView(LoginRequiredHTMXMixin, CommentGetMethodMixin, CreateView):
    model = Comment
    form_class = CommentCreateForm
    template_name = "posts/comments/_comment_root_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        post_id = self.kwargs.get("post_pk")
        kwargs["post"] = get_object_or_404(Post, id=post_id)
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

        response = render(self.request, self.template_name, context)
        response["HX-Trigger"] = "commentsUpdated, commentRootFormSuccess"
        return response

    def form_invalid(self, form):
        context = self.get_context_data(form, form_valid=False)

        response = render(self.request, self.template_name, context)
        response["HX-Trigger"] = "commentRootFormError"
        return response


class CommentChildCreateView(CommentRootCreateView):
    template_name = "posts/comments/_comment_child_form.html"

    def _add_errors_to_messages(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                if field == "__all__":
                    # ошибки на уровне формы
                    messages.error(self.request, f"Ошибка: {error}")
                else:
                    # ошибки конкретного поля
                    messages.error(self.request, f'Ошибка в "{form.fields[field].label}": {error}')

        # Редирект обратно на страницу поста
        return form.post.get_absolute_url()

    def form_valid(self, form):
        response = super().form_valid(form)

        reply_to = form.cleaned_data.get("reply_to")

        if not reply_to:
            self._add_errors_to_messages(form)

        # Определяется commentId для события
        comment_id = reply_to.id

        # Передаются данные в формате JSON для HX-Trigger
        response["HX-Trigger"] = json.dumps(
            {"commentsUpdated": {}, "commentChildFormSuccess": {"commentId": comment_id}}
        )

        return response

    def form_invalid(self, form):
        response = super().form_invalid(form)

        reply_to = form.cleaned_data.get("reply_to")

        if not reply_to:
            self._add_errors_to_messages(form)
            response["HX-Redirect"] = self.request.path
            return response

        comment_id = reply_to.id

        response["HX-Trigger"] = json.dumps({"commentChildFormError": {"commentId": comment_id}})

        return response


class CommentUpdateView(
    LikeAnnotationsMixin,
    LoginRequiredHTMXMixin,
    HTMXHandle404Mixin,
    CommentGetMethodMixin,
    UpdateView,
):
    model = Comment
    form_class = CommentUpdateForm
    pk_url_kwarg = "comment_pk"
    template_name = "posts/comments/_comment_card.html"

    def get_object(self, queryset=None):
        queryset = queryset or self.model.objects.select_related("author", "post")
        obj = super().get_object(queryset=queryset)
        obj = self.annotate_object(obj)
        return obj

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(**kwargs)
        context.pop("form")
        context = {
            "comment_form": form,
            "comment": self.object,
            "post": self.object.post,
        }
        return context

    def form_valid(self, form):
        self.object = form.save()
        context = self.get_context_data(form)

        response = render(self.request, self.template_name, context)
        response["HX-Trigger"] = json.dumps({"commentUpdateSuccess": {"commentId": self.object.id}})
        return response

    def form_invalid(self, form):
        context = self.get_context_data(form)

        response = render(self.request, self.template_name, context)
        response["HX-Trigger"] = json.dumps({"commentUpdateError": {"commentId": self.object.id}})
        return response


class CommentDeleteView(
    LoginRequiredHTMXMixin, HTMXHandle404Mixin, CommentGetMethodMixin, DeleteView
):
    model = Comment
    pk_url_kwarg = "comment_pk"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return HttpResponse(headers={"HX-Trigger": "commentsUpdated"})


class ToggleLikeBaseView(LoginRequiredHTMXMixin, View):
    model: type[models.Model]
    pk_url_kwarg: str = "pk"

    def _get_toggle_like_url(self, liked_object):
        return reverse_lazy("home")

    def post(self, request, *args, **kwargs):
        liked_object = get_object_or_404(self.model, pk=kwargs[self.pk_url_kwarg])

        with transaction.atomic():
            liked_object = self.model.objects.select_for_update().get(pk=kwargs[self.pk_url_kwarg])
            like, created = liked_object.likes.get_or_create(user=request.user)
            if not created:
                like.delete()

        context = {
            "toggle_like_url": self._get_toggle_like_url(liked_object),
            "liked_object": liked_object,
            "likes_count": liked_object.likes.count(),
            "user_has_liked": created,
        }

        response = render(request, "posts/likes/_like-button.html", context)

        return response


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
