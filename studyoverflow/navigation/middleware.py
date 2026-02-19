import logging


logger = logging.getLogger(__name__)


class UserActivityMiddleware:
    """
    Промежуточное ПО для логирования активности пользователей.

    Логирует данные о запросе: данные пользователя, метод, путь и статус ответа.
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

        Логирует данные о запросе и ответе, пропускает логирование запросов по исключённым путям.
        """
        skip_path_prefixes = ["/favicon.ico"]
        if any(request.path.startswith(path) for path in skip_path_prefixes):
            return self.get_response(request)

        response = self.get_response(request)

        logger.info(
            "Отправлен запрос к ресурсу.",
            extra={
                "user_id": request.user.pk if request.user.is_authenticated else None,
                "username": request.user.username if request.user.is_authenticated else None,
                "method": request.method,
                "path": request.path,
                "response_status_code": response.status_code,
                "event_type": "request",
            },
        )

        return response
