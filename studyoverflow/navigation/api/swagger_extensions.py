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
            "description": "Аутентификация через сессию в cookie клиента. "
            "В поле Value вводится только сама сессия.",
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
