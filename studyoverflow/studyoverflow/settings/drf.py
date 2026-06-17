from datetime import timedelta

from .base import SECRET_KEY


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
}

# Настройки JWT токена
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),  # Время жизни access token
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),  # Время жизни refresh token
    "ROTATE_REFRESH_TOKENS": True,  # Выдавать новый refresh при обновлении
    "BLACKLIST_AFTER_ROTATION": True,  # Добавлять старый refresh в blacklist
    "UPDATE_LAST_LOGIN": True,  # Обновлять user.last_login при логине
    "ALGORITHM": "HS256",  # Алгоритм подписи JWT
    "SIGNING_KEY": SECRET_KEY,  # Секретный ключ для подписи
    "VERIFYING_KEY": "",  # Публичный ключ при алгоритмах RS256 или ES256
    "AUDIENCE": None,  # aud, для какого именно сервиса выдан токен
    "ISSUER": None,  # iss, какой сервис выпустил токен
    "JSON_ENCODER": None,  # Кастомный JSON_ENCODER
    "JWK_URL": None,  # URL сервиса с публичными ключами, альтернатива локальному VERIFYING_KEY (JWK - JSON Web Key)
    "LEEWAY": 0,  # Погрешность времени в секундах, на сколько могут быть просрочены токены
    "AUTH_HEADER_TYPES": ("Bearer",),  # Префикс в Authorization: Bearer <token>
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",  # Имя HTTP-заголовка
    "USER_ID_FIELD": "id",  # Поле модели User для идентификации
    "USER_ID_CLAIM": "user_id",  # Имя ключа в payload токена, где хранится id пользователя
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",  # Правило проверки пользователя (например, существует и is_active)
    "AUTH_TOKEN_CLASSES": (
        "rest_framework_simplejwt.tokens.AccessToken",
    ),  # Классы токенов, принимаемые бекендом для авторизации
    "TOKEN_TYPE_CLAIM": "token_type",  # Claim с типом токена: access/refresh
    "JTI_CLAIM": "jti",  # Уникальный идентификатор токена (есть и у access, и у refresh)
}
