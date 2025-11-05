from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Prefetch
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from posts.forms import CommentCreateForm, PostCreateForm
from posts.models import Comment, Post
from posts.services.infrastructure import PostTagMixin


class PostListView(ListView):
    model = Post
    template_name = "posts/post_list.html"
    context_object_name = "posts"
    paginate_by = 7
    extra_context = {"section_of_menu_selected": "posts:list"}


class PostCreateView(PostTagMixin, LoginRequiredMixin, CreateView):
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


class PostDetailView(DetailView):
    model = Post
    template_name = "posts/post_detail.html"
    context_object_name = "post"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Пустая форма в шаблон для написания комментария
        context["comment_form"] = CommentCreateForm()
        return context

    def get_queryset(self):
        return Post.objects.prefetch_related(
            Prefetch(
                "comments",
                queryset=Comment.objects.roots().prefetch_related(
                    Prefetch("child_comments", queryset=Comment.objects.order_by("time_create"))
                ),
            )
        )


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentCreateForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        post_id = self.kwargs.get("post_pk")
        kwargs["post"] = get_object_or_404(Post, id=post_id)
        return kwargs

    def form_valid(self, form):
        form.instance.post = form.post
        form.instance.author = self.request.user
        return super().form_valid(form)

    def form_invalid(self, form):
        # Ошибки формы в messages, если они имеются
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'Ошибка в "{form.fields[field].label}": {error}')

        # Редирект обратно на страницу поста
        return self._redirect_to_post_detail()

    def get_success_url(self):
        return self.object.post.get_absolute_url()

    def get(self, request, *args, **kwargs):
        return self._redirect_to_post_detail()

    def _redirect_to_post_detail(self):
        """
        Редирект на страницу поста.
        """
        post = get_object_or_404(Post, id=self.kwargs.get("post_pk"))
        return HttpResponseRedirect(post.get_absolute_url())


class PostUpdateView(PostTagMixin, UpdateView):
    model = Post
    form_class = PostCreateForm
    template_name = "posts/post_edit.html"
    context_object_name = "post"
