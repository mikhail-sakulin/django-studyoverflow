from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import TemplateView


class IndexTemplateView(TemplateView):
    """Главная страница сайта."""

    template_name = "navigation/index.html"


def page_not_found(request, exception):
    """Страница ошибки 404 (Страница не найдена)."""
    if request.path.startswith("/api/"):
        return JsonResponse(
            {"detail": "Неверный адрес, или запрашиваемый контент не существует."}, status=404
        )

    return render(request, "http_statuses/404.html", status=404)


def permission_denied(request, exception):
    """Страница ошибки 403 (Доступ запрещен)."""
    if request.path.startswith("/api/"):
        return JsonResponse({"detail": "У вас нет прав для выполнения этого действия."}, status=403)

    return render(request, "http_statuses/403.html", status=403)


def csrf_failure(request, reason=""):
    """Страница ошибки проверки CSRF-токена."""
    if request.path.startswith("/api/"):
        return JsonResponse({"detail": f"Ошибка проверки CSRF-токена: {reason}."}, status=403)

    return render(request, "http_statuses/403_csrf.html", status=403)


def server_error(request):
    """Страница ошибки 500 (Внутренняя ошибка сервера)."""
    if request.path.startswith("/api/"):
        return JsonResponse({"detail": "Внутренняя ошибка сервера."}, status=500)

    return render(request, "http_statuses/500.html", status=500)


def bad_request(request, exception):
    """Страница ошибки 400 (Некорректный запрос)."""
    if request.path.startswith("/api/"):
        return JsonResponse({"detail": "Некорректный запрос."}, status=400)

    return render(request, "http_statuses/400.html", status=400)


def unauthorized(request, exception):
    """
    Страница ошибки 401 (Неавторизованный доступ).

    В текущей версии проекта не используется.
    """
    if request.path.startswith("/api/"):
        return JsonResponse(
            {"detail": "Учетные данные не предоставлены или недействительны."}, status=401
        )

    return render(request, "http_statuses/401.html", status=401)


def method_not_allowed(request, exception):
    """
    Страница ошибки 405 (Метод не разрешен).

    В текущей версии проекта не используется.
    """
    if request.path.startswith("/api/"):
        return JsonResponse(
            {"detail": f"Метод {request.method} не разрешен для этого эндпоинта."}, status=405
        )

    return render(request, "http_statuses/405.html", status=405)
