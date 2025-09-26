from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView
from posts.forms import PostCreateForm


def index(request):
    """
    Главная страница сайта.
    """
    return render(request, "posts/index.html")


def show_posts(request):
    """
    Страница отображения всех постов.
    """
    return render(request, "posts/posts.html")


class PostCreateView(CreateView):
    """
    Класс-представление для создания нового поста.
    """

    form_class = PostCreateForm
    template_name = "posts/create_post.html"
    success_url = reverse_lazy("home")


def users(request):
    """
    Страница демонстрации всех пользователей.
    """
    return render(request, "posts/users.html")
