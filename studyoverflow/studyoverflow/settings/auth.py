from datetime import timedelta

from .base import SECRET_KEY, env


# ----------------------------------------
# Модель пользователя (User)
# ----------------------------------------

# Кастомная модель пользователя
AUTH_USER_MODEL = "users.User"


# ----------------------------------------
# Редиректы после логина/логаута
# ----------------------------------------

# URL страницы для логина
LOGIN_URL = "/users/login/"

# URL для редиректа после успешного логина
LOGIN_REDIRECT_URL = "home"

# URL для редиректа после логаута
LOGOUT_REDIRECT_URL = "home"


# ----------------------------------------
# Валидация паролей
# ----------------------------------------

# Стандартные валидаторы Django
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# ----------------------------------------
# Allauth настройки
# ----------------------------------------

# Бэкенды аутентификации
AUTHENTICATION_BACKENDS = [
    # Позволяет логин через стандартный ModelBackend и также проверяет,
    # что пользователь не заблокирован (user.is_blocked == False)
    "users.authentication_backends.CustomAuthenticationBackend",
    # Позволяет логин через allauth (через соцсети) и также проверяет,
    # что пользователь не заблокирован (user.is_blocked == False)
    "users.authentication_backends.CustomAllAuthAuthenticationBackend",
]

# Кастомные адаптеры
SOCIALACCOUNT_ADAPTER = "users.adapters.CustomSocialAccountAdapter"
ACCOUNT_ADAPTER = "users.adapters.AllauthMessageAdapter"

# Поля, обязательные при регистрации через allauth
ACCOUNT_SIGNUP_FIELDS = ["username*", "email*", "password1*", "password2*"]

# Отключение верификации email (можно включить по необходимости)
SOCIALACCOUNT_EMAIL_VERIFICATION = "none"

# Автоматическая регистрация пользователя при первом входе через социальный аккаунт
SOCIALACCOUNT_AUTO_SIGNUP = True


# ----------------------------------------
# Социальные провайдеры
# ----------------------------------------

# Настройки для OAuth-провайдеров
SOCIALACCOUNT_PROVIDERS = {
    "github": {
        "APPS": [
            {
                "client_id": env("SOCIAL_AUTH_GITHUB_ID"),
                "secret": env("SOCIAL_AUTH_GITHUB_SECRET"),
            },
        ],
        "SCOPE": [
            "read:user",
            "user:email",
        ],
    },
    "google": {
        "APPS": [
            {
                "client_id": env("SOCIAL_AUTH_GOOGLE_ID"),
                "secret": env("SOCIAL_AUTH_GOOGLE_SECRET"),
                "key": "",
            },
        ],
        "SCOPE": [
            "profile",
            "email",
        ],
        "AUTH_PARAMS": {
            "access_type": "online",
        },
        "OAUTH_PKCE_ENABLED": True,
    },
    "yandex": {
        "APPS": [
            {
                "client_id": env("SOCIAL_AUTH_YANDEX_ID"),
                "secret": env("SOCIAL_AUTH_YANDEX_SECRET"),
            }
        ],
        "SCOPE": [
            "login:info",
            "login:avatar",
        ],
    },
    "vk": {
        "APPS": [
            {
                "client_id": env("SOCIAL_AUTH_VK_ID"),
                "secret": env("SOCIAL_AUTH_VK_SECRET"),
            }
        ],
        "SCOPE": ["email", "public_profile"],
        "VERSION": "5.131",
    },
}


# ----------------------------------------
# Настройки JWT токенов (simplejwt и dj_rest_auth)
# ----------------------------------------

# Настройки JWT токенов simplejwt
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

# Настройки dj_rest_auth
REST_AUTH = {
    "USE_JWT": True,  # Выдача JWT вместо DRF токенов
    "JWT_AUTH_COOKIE": "studyoverflow-access",  # Имя COOKIE для access-токена
    "JWT_AUTH_REFRESH_COOKIE": "studyoverflow-refresh",  # Имя COOKIE для refresh-токена
    "JWT_AUTH_HTTPONLY": False,  # False, если токен забирает фронтенд сам из JSON
}
