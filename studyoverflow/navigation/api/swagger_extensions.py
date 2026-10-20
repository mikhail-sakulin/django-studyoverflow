"""
Модуль расширений OpenAPI. Содержит кастомные схемы аутентификации (OpenApiAuthenticationExtension).
"""

from drf_spectacular.extensions import OpenApiAuthenticationExtension


class CustomSessionScheme(OpenApiAuthenticationExtension):
    """
    Схема OpenAPI для аутентификации через сессию.
    """

    target_class = "users.api.authentication.CustomSessionAuthentication"
    name = "sessionAuth"

    def get_security_definition(self, auto_schema):
        """Возвращает спецификацию аутентификации."""
        return {
            "type": "apiKey",
            "in": "cookie",
            "name": "sessionid",
            "description": (
                "Аутентификация через сессию в cookie клиента. В Swagger UI поле Value не работает:"
                " заголовок Cookie входит в список запрещённых для fetch/XHR (HTTP-запросы из JS) "
                "заголовков (forbidden header names), поэтому браузер не отправит введённое "
                "значение. Для API-аутентификации через сессию нужно отправить запрос "
                "POST /api/v1/auth/session-login/ в Swagger (также подойдет web-аутентификация). "
                "Для POST/PUT/PATCH/DELETE запросов при сессии дополнительно нужен заголовок "
                "X-CSRFToken со значением куки csrftoken. Swagger UI прикрепляет его автоматически,"
                " но берёт значение при загрузке страницы, поэтому после аутентификации через "
                "сессию страницу Swagger нужно перезагрузить."
            ),
        }


class CustomTokenScheme(OpenApiAuthenticationExtension):
    """
    Схема OpenAPI для аутентификации через DRF токен.
    """

    target_class = "users.api.authentication.CustomTokenAuthentication"
    name = "tokenAuth"

    def get_security_definition(self, auto_schema):
        """Возвращает спецификацию аутентификации."""
        return {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": 'Аутентификация через DRF токен. В поле Value вводится "Token <токен>".',
        }


class CustomJWTScheme(OpenApiAuthenticationExtension):
    """
    Схема OpenAPI для аутентификации через JWT токен.
    """

    target_class = "users.api.authentication.CustomJWTAuthentication"
    name = "jwtAuth"

    def get_security_definition(self, auto_schema):
        """Возвращает спецификацию аутентификации."""
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Аутентификация через JWT токен. В поле Value вводится только "
            'сам токен. Swagger UI автоматически подставит "Bearer " при '
            "формировании заголовка Authorization.",
        }
