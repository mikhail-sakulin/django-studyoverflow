from django.shortcuts import render
from django.views.generic import TemplateView


class IndexTemplateView(TemplateView):
    template_name = "navigation/index.html"


def page_not_found(request, exception):
    return render(request, "http_statuses/404.html", status=404)


def permission_denied(request, exception):
    return render(request, "http_statuses/403.html", status=403)


def csrf_failure(request, reason=""):
    return render(request, "http_statuses/403_csrf.html", status=403)


def server_error(request):
    return render(request, "http_statuses/500.html", status=500)


def bad_request(request, exception):
    return render(request, "http_statuses/400.html", status=400)


def unauthorized(request, exception):
    return render(request, "http_statuses/401.html", status=401)


def method_not_allowed(request, exception):
    return render(request, "http_statuses/405.html", status=405)
