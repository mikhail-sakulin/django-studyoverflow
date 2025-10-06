from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView
from posts.forms import PostCreateForm
from posts.models import LowercaseTag, Post


def index(request):
    """
    Главная страница сайта.
    """
    return render(request, "posts/index.html")


class PostListView(ListView):
    model = Post
    template_name = "posts/post_list.html"
    context_object_name = "posts"
    paginate_by = 7


class PostCreateView(CreateView):
    """
    Класс-представление для создания нового поста.
    """

    form_class = PostCreateForm
    template_name = "posts/create_post.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        post = form.save()
        tags = form.cleaned_data["tags"]
        post.tags.set(tags)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["all_tags"] = LowercaseTag.objects.all().order_by("name")
        return context


class PostDetailView(DetailView):
    model = Post
    template_name = "posts/post_detail.html"
    context_object_name = "post"


def users(request):
    """
    Страница демонстрации всех пользователей.
    """
    return render(request, "posts/users.html")
