from .base import DEBUG


REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    # Кастомная пагинация для api запросов.
    "DEFAULT_PAGINATION_CLASS": "navigation.api.pagination.CustomPageNumberPagination",
    # Поддерживаемые способы аутентификации
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "users.api.authentication.CustomTokenAuthentication",
        "users.api.authentication.CustomJWTAuthentication",
        "users.api.authentication.CustomSessionAuthentication",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# Browsable API (веб-интерфейс DRF) только если DEBUG == True
if DEBUG:
    REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"].append(  # type: ignore
        "rest_framework.renderers.BrowsableAPIRenderer"
    )

SPECTACULAR_SETTINGS = {
    # Базовая информация
    "TITLE": "StudyOverflow API",
    "DESCRIPTION": "Документация API эндпоинтов проекта StudyOverflow, используется DRF "
    " для API, drf-spectacular для OpenAPI. "
    "Web версия реализована с помощью классического Django.",
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

# Настройки dj_rest_auth в модуле .auth
