import json

from django.contrib import messages
from django.db.models import Prefetch
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from posts.forms import CommentCreateForm, CommentUpdateForm, PostCreateForm
from posts.models import Comment, Post
from posts.services.infrastructure import (
    CommentGetMethodMixin,
    HTMXHandle404Mixin,
    LoginRequiredHTMXMixin,
    PostQuerysetMixin,
    PostTagMixin,
)


class PostListView(PostQuerysetMixin, ListView):
    model = Post
    template_name = "posts/post_list.html"
    context_object_name = "posts"
    paginate_by = 7
    extra_context = {"section_of_menu_selected": "posts:list"}


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


class PostDetailView(PostQuerysetMixin, DetailView):
    model = Post
    template_name = "posts/post_detail.html"
    context_object_name = "post"

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


class CommentListView(ListView):
    model = Comment
    template_name = "posts/comments/comment_list.html"
    context_object_name = "root_comments"

    def _get_post_object(self):
        if not hasattr(self, "_post_object"):
            post_pk = self.kwargs.get("post_pk")
            self._post_object = get_object_or_404(Post, pk=post_pk)
        return self._post_object

    def get_queryset(self):
        post = self._get_post_object()
        return post.comments.roots().prefetch_related(
            Prefetch("child_comments", queryset=Comment.objects.order_by("-time_create"))
        )

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
    LoginRequiredHTMXMixin, HTMXHandle404Mixin, CommentGetMethodMixin, UpdateView
):
    model = Comment
    form_class = CommentUpdateForm
    pk_url_kwarg = "comment_pk"
    template_name = "posts/comments/_comment_card.html"

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


class ToggleLikePostView(LoginRequiredHTMXMixin, View):
    def post(self, request, *args, **kwargs):
        post = get_object_or_404(Post, pk=kwargs["post_pk"])
        like, created = post.likes.get_or_create(user=request.user)
        if not created:
            like.delete()

        context = {
            "post": post,
            "likes_count": post.likes.count(),
            "user_has_liked": created,
        }

        response = render(request, "posts/likes/_like-button.html", context)

        return response
