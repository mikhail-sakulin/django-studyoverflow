from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
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
        return Post.objects.prefetch_related("comments", "comments__child_comments")

    def post(self, request, *args, **kwargs):
        # Получение объекта (post) на основе pk или slug
        self.object = self.get_object()
        form = CommentCreateForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = self.object
            comment.author = request.user

            # Связь с родительским комментарием, если он есть
            parent_id = form.cleaned_data.get("parent_comment")
            if parent_id:
                try:
                    comment.parent_comment = Comment.objects.get(id=parent_id)
                except Comment.DoesNotExist:
                    # Если родительский комментарий не найден, то остается None
                    pass

            comment.save()
            return redirect(self.object.get_absolute_url())

        context = self.get_context_data(comment_form=form)
        return self.render_to_response(context)


class PostUpdateView(PostTagMixin, UpdateView):
    model = Post
    form_class = PostCreateForm
    template_name = "posts/post_edit.html"
    context_object_name = "post"
