from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect
from users.services.infrastructure import set_user_online


class OnlineStatusMiddleware:
    """
    Промежуточное ПО (Middleware) для отслеживания активности пользователей.

    Обновляет статус "online" авторизованного пользователя в Redis при каждом HTTP-запросе.
    """

    def __init__(self, get_response):
        """
        Инициализация middleware.

        Args:
            get_response: Колбэк для получения ответа от следующего слоя middleware или view.
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        Обработка входящего запроса / исходящего ответа.

        После обработки запроса обновляет онлайн статус в Redis,
        если пользователь аутентифицирован.
        """
        response = self.get_response(request)

        if request.user.is_authenticated and request.user.id:
            set_user_online(request.user.id)

        return response


class BlockedUserMiddleware:
    """
    Промежуточное ПО (Middleware) для принудительного
    завершения сессии (logout) заблокированных пользователей.

    Проверяет флаг блокировки пользователя перед обработкой запроса. Если пользователь
    заблокирован, вызывается logout, и он перенаправляется на главную страницу.
    """

    def __init__(self, get_response):
        """
        Инициализация middleware.

        Args:
            get_response: Колбэк для получения ответа от следующего слоя middleware или view.
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        Обработка входящего запроса / исходящего ответа.

        Если залогиненный пользователь помечен как заблокированный (is_blocked),
        прерывает цепочку выполнения, очищает сессию, перенаправляет на главную страницу
        и выводит сообщение об ошибке.
        """
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
