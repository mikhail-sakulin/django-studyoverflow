from django.shortcuts import render


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


def create_post(request):
    """
    Страница создания постов.
    """
    return render(request, "posts/create_post.html")


def users(request):
    """
    Страница демонстрации всех пользователей.
    """
    return render(request, "posts/users.html")
