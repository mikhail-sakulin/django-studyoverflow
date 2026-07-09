# from .base import DEBUG


REST_FRAMEWORK = {
    # Кастомный обработчик исключений для DRF.
    "EXCEPTION_HANDLER": "navigation.api.exceptions.custom_exception_handler",
    # Кастомная пагинация для api запросов.
    "DEFAULT_PAGINATION_CLASS": "navigation.api.pagination.CustomPageNumberPagination",
    # Поддерживаемые способы аутентификации
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    # "DEFAULT_AUTHENTICATION_CLASSES": [
    #     "users.api.authentication.CustomTokenAuthentication",
    #     "users.api.authentication.CustomJWTAuthentication",
    #     "users.api.authentication.CustomSessionAuthentication",
    # ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    # Базовая информация
    "TITLE": "StudyOverflow API",
    "DESCRIPTION": "Документация эндпоинтов проекта StudyOverflow.",
    "VERSION": "1.0",
    # Права доступа к документации в зависимости от DEBUG
    "SERVE_PERMISSIONS": (
        ["rest_framework.permissions.AllowAny"]
        if True  # Для демонстрации API проекта установлено True, в продакшене нужно if DEBUG
        else ["rest_framework.permissions.IsAdminUser"]
    ),
    # Для Request и для Response генерируются разные схемы сериализаторов,
    # нужно, например, для загрузки аватара пользователя как файла
    "COMPONENT_SPLIT_REQUEST": True,
    # Исключает эндпоинт схемы (schema/) из генерируемой API документации
    "SERVE_INCLUDE_SCHEMA": False,
}
