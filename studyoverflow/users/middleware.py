from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect
from users.services.infrastructure import set_user_online


class OnlineStatusMiddleware:
    """
    Middleware обновляет статус "online" пользователя в Redis при каждом HTTP-запросе.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated:
            set_user_online(request.user.id)

        return response


class BlockedUserMiddleware:
    """
    Разлогинивает пользователя, если его заблокировали во время сессии.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user

        if user.is_authenticated and user.is_blocked:
            logout(request)

            messages.error(
                request,
                "Ваш аккаунт был заблокирован администрацией. "
                "Совершен принудительный выход из аккаунта.",
            )
            return redirect("home")

        return self.get_response(request)
