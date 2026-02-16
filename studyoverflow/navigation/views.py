from django.shortcuts import render
from django.views.generic import TemplateView


class IndexTemplateView(TemplateView):
    """Главная страница сайта."""

    template_name = "navigation/index.html"


def page_not_found(request, exception):
    """Страница ошибки 404 (Страница не найдена)."""
    return render(request, "http_statuses/404.html", status=404)


def permission_denied(request, exception):
    """Страница ошибки 403 (Доступ запрещен)."""
    return render(request, "http_statuses/403.html", status=403)


def csrf_failure(request, reason=""):
    """Страница ошибки проверки CSRF-токена."""
    return render(request, "http_statuses/403_csrf.html", status=403)


def server_error(request):
    """Страница ошибки 500 (Внутренняя ошибка сервера)."""
    return render(request, "http_statuses/500.html", status=500)


def bad_request(request, exception):
    """Страница ошибки 400 (Некорректный запрос)."""
    return render(request, "http_statuses/400.html", status=400)


def unauthorized(request, exception):
    """Страница ошибки 401 (Неавторизованный доступ)."""
    return render(request, "http_statuses/401.html", status=401)


def method_not_allowed(request, exception):
    """Страница ошибки 405 (Метод не разрешен)."""
    return render(request, "http_statuses/405.html", status=405)
