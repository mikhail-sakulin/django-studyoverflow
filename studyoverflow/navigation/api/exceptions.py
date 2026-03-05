import logging

from rest_framework.views import exception_handler


logger = logging.getLogger("django.request")


def custom_exception_handler(exc, context):
    """
    Кастомный обработчик исключений для DRF.

    Расширяет стандартный обработчик DRF, добавляя детальное логирование
    ошибок валидации (HTTP 400).
    """
    response = exception_handler(exc, context)

    if response is not None and response.status_code == 400:
        view = context.get("view")
        view_name = view.__class__.__name__ if view else "UnknownView"
        request = context.get("request")

        # Определение пользователя
        if request and request.user and request.user.is_authenticated:
            username = request.user.username
            user_id = request.user.pk
        else:
            username = "Anonymous"
            user_id = None

        # Логирование
        logger.warning(
            f"Validation Error in {view_name} | User: {username} | Errors: {response.data}.",
            extra={
                "status_code": 400,
                "view_name": view_name,
                "username": username,
                "user_id": user_id,
                "validation_errors": response.data,
            },
        )

    return response
